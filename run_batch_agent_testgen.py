#!/usr/bin/env python3
"""Batch agentic test generation using Qwen Code in Docker.

Processes SWE-CARE instances in parallel. Each instance gets one Qwen Code
invocation that generates validation tests for all selected review comments.

Usage:
  python run_batch_agent_testgen.py --limit 5 --workers 2
  python run_batch_agent_testgen.py --repo tobymao/sqlglot
  python run_batch_agent_testgen.py --comments-file targets.csv
  python run_batch_agent_testgen.py --no-resume
"""

import argparse
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from execution.container_runtime import docker_image_exists
from pipeline import dataset_utils
from pipeline.llm_client import LLMUsage
from run_agent_testgen import (
    DEFAULT_DOCKER_IMAGE_MAP_FILE,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QWEN_SETTINGS,
    load_comment_selection_file,
    process_instance,
    process_instance_multi,
)
from run_batch_testgen import (
    load_docker_image_map,
    load_existing_result,
    write_summary,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _selected_comment_count(
    instance: dict,
    selected_comment_indices: set[int] | None,
) -> int:
    if selected_comment_indices is None:
        return len(instance.get("reference_review_comments", []))
    return sum(
        1
        for index, _comment in enumerate(instance.get("reference_review_comments", []))
        if index in selected_comment_indices
    )


def _error_result(
    instance: dict,
    model: str,
    error: str,
    selected_comment_indices: set[int] | None = None,
) -> dict:
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "agent": "qwen-code",
        "model": model,
        "usage": LLMUsage().to_dict(),
        "num_comments": _selected_comment_count(instance, selected_comment_indices),
        "results": [],
        "overall_expected_failure_rate": 0.0,
        "error": error,
    }


def _load_instances_file(instances_file: Path) -> set[str]:
    if not instances_file.exists():
        raise FileNotFoundError(f"Instances file not found: {instances_file}")
    wanted_ids = set()
    for line in instances_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            wanted_ids.add(line)
    return wanted_ids


def main():
    parser = argparse.ArgumentParser(
        description="Batch test generation using one Qwen Code run per instance"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Only process instances for this repo (e.g. 'tobymao/sqlglot')",
    )
    parser.add_argument(
        "--instances-file",
        type=str,
        default=None,
        help="File with instance IDs to process (one per line, # comments ignored)",
    )
    parser.add_argument(
        "--comments-file",
        type=str,
        default=None,
        help="CSV of comment targets with instance_id and comment_index columns",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of instances to process",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Where to save results (default: {DEFAULT_OUTPUT_DIR}/)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Qwen model to use (default: use Qwen configured default)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1)",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=3,
        help=(
            "Number of independent generation runs per instance (default: 3). "
            "Set to 1 to use the original single-run process_instance path."
        ),
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-process all instances even if results already exist",
    )
    parser.add_argument(
        "--skip-execution",
        action="store_true",
        help="Generate tests only, don't run them",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and save prompt.txt/trajectory.json, then stop before invoking Qwen",
    )
    parser.add_argument(
        "--docker-image-map",
        "--docker-image-map-file",
        dest="docker_image_map",
        type=str,
        default=DEFAULT_DOCKER_IMAGE_MAP_FILE,
        help=(
            "CSV mapping file with selected Docker images "
            f"(default: {DEFAULT_DOCKER_IMAGE_MAP_FILE})"
        ),
    )
    parser.add_argument(
        "--qwen-settings",
        "--credentials",
        dest="qwen_settings",
        type=str,
        default=str(DEFAULT_QWEN_SETTINGS),
        help=f"Path to Qwen settings.json (default: {DEFAULT_QWEN_SETTINGS})",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    docker_image_map_file = Path(args.docker_image_map)
    qwen_settings_path = Path(args.qwen_settings)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = not args.no_resume

    try:
        docker_image_map = load_docker_image_map(docker_image_map_file)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)

    comment_selection: dict[str, set[int]] = {}
    if args.comments_file:
        try:
            comment_selection = load_comment_selection_file(Path(args.comments_file))
        except (FileNotFoundError, ValueError) as exc:
            logger.error(str(exc))
            sys.exit(1)

    all_instances = dataset_utils.load_instances(repo=args.repo)
    logger.info("Loaded %d instances from local dataset", len(all_instances))

    if args.instances_file:
        try:
            wanted_ids = _load_instances_file(Path(args.instances_file))
        except FileNotFoundError as exc:
            logger.error(str(exc))
            sys.exit(1)
        before = len(all_instances)
        all_instances = [
            instance
            for instance in all_instances
            if instance["instance_id"] in wanted_ids
        ]
        logger.info(
            "Filtered to %d instances from %s (%d IDs, %d matched)",
            len(all_instances),
            args.instances_file,
            len(wanted_ids),
            len(all_instances),
        )
        missing = wanted_ids - {i["instance_id"] for i in all_instances}
        if missing:
            logger.warning("Instance IDs not found in dataset: %s", missing)
        logger.debug("Instance filter removed %d entries", before - len(all_instances))

    if comment_selection:
        selected_instance_ids = set(comment_selection)
        all_instances = [
            instance
            for instance in all_instances
            if instance["instance_id"] in selected_instance_ids
        ]
        logger.info(
            "Filtered to %d instances from %s (%d target instances)",
            len(all_instances),
            args.comments_file,
            len(selected_instance_ids),
        )
        missing = selected_instance_ids - {i["instance_id"] for i in all_instances}
        if missing:
            logger.warning("Comment target instances not found in dataset: %s", missing)

    if args.limit and len(all_instances) > args.limit:
        all_instances = all_instances[: args.limit]
        logger.info("Limited to %d instances", len(all_instances))

    if not all_instances:
        logger.error("No instances found.")
        sys.exit(1)

    if not qwen_settings_path.exists():
        logger.warning(
            "Qwen settings file not found: %s (containers may fail to authenticate)",
            qwen_settings_path,
        )

    all_results: list[dict] = []
    to_process: list[dict] = []

    for instance in all_instances:
        iid = instance["instance_id"]
        selected_indices = comment_selection.get(iid)

        if resume:
            existing = load_existing_result(output_dir, iid)
            if existing is not None:
                logger.info("Skipping (already done): %s", iid)
                all_results.append(existing)
                continue

        docker_image = docker_image_map.get(iid)
        if not docker_image:
            logger.warning("[%s] Docker image mapping not found, skipping", iid)
            all_results.append(
                _error_result(
                    instance,
                    args.model,
                    f"Docker image mapping not found in {docker_image_map_file}",
                    selected_indices,
                )
            )
            continue
        if not docker_image_exists(docker_image):
            logger.warning("[%s] Docker image not found locally: %s", iid, docker_image)
            all_results.append(
                _error_result(
                    instance,
                    args.model,
                    f"Docker image not found: {docker_image}",
                    selected_indices,
                )
            )
            continue

        to_process.append(instance)

    if not to_process:
        logger.info("All instances already processed or skipped.")
        summary = write_summary(output_dir, all_results, 0.0)
        logger.info(
            "Summary: %d instances, %d tests, %d expected failures observed (%.1f%%)",
            summary["total_instances"],
            summary["total_tests_generated"],
            summary["total_expected_failures_observed"],
            summary["overall_expected_failure_rate"] * 100,
        )
        return

    start_time = time.time()
    processed = 0
    lock = threading.Lock()

    logger.info(
        "Processing %d instance(s) with %d worker(s)",
        len(to_process),
        args.workers,
    )

    def _process_one(instance: dict) -> dict:
        iid = instance["instance_id"]
        try:
            if args.num_samples > 1:
                return process_instance_multi(
                    instance=instance,
                    output_dir=output_dir,
                    model=args.model,
                    docker_image=docker_image_map[iid],
                    qwen_settings_path=qwen_settings_path,
                    selected_comment_indices=comment_selection.get(iid),
                    num_samples=args.num_samples,
                    skip_execution=args.skip_execution,
                    dry_run=args.dry_run,
                )
            return process_instance(
                instance=instance,
                output_dir=output_dir,
                model=args.model,
                docker_image=docker_image_map[iid],
                qwen_settings_path=qwen_settings_path,
                selected_comment_indices=comment_selection.get(iid),
                skip_execution=args.skip_execution,
                dry_run=args.dry_run,
            )
        except Exception:
            logger.exception("[%s] Error processing instance", iid)
            return _error_result(
                instance,
                args.model,
                "Processing failed",
                comment_selection.get(iid),
            )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_inst = {
            executor.submit(_process_one, inst): inst for inst in to_process
        }

        for future in as_completed(future_to_inst):
            inst = future_to_inst[future]
            result = future.result()

            with lock:
                all_results.append(result)
                processed += 1
                count = processed

            logger.info(
                "[%d/%d] Completed %s: %d tests, %.1f%% expected-failure rate",
                count,
                len(to_process),
                inst["instance_id"],
                sum(1 for c in result.get("results", []) if c.get("test_code")),
                result.get("overall_expected_failure_rate", 0.0) * 100,
            )

            if count % 10 == 0:
                with lock:
                    elapsed_so_far = time.time() - start_time
                    summary = write_summary(output_dir, list(all_results), elapsed_so_far)
                logger.info(
                    "Progress: %d/%d instances, %d tests generated, %d expected failures observed (%.1f%%)",
                    len(all_results),
                    len(all_instances),
                    summary["total_tests_generated"],
                    summary["total_expected_failures_observed"],
                    summary["overall_expected_failure_rate"] * 100,
                )

    total_elapsed = time.time() - start_time
    summary = write_summary(output_dir, all_results, total_elapsed)
    logger.info(
        "=== DONE === %d instances, %d tests generated, %d expected failures observed (%.1f%%), "
        "%d errors, %.0fs elapsed",
        summary["total_instances"],
        summary["total_tests_generated"],
        summary["total_expected_failures_observed"],
        summary["overall_expected_failure_rate"] * 100,
        summary["total_errors"],
        total_elapsed,
    )
    logger.info("Summary: %s", output_dir / "summary.json")


if __name__ == "__main__":
    main()
