#!/usr/bin/env python3
"""Batch intent-guided agent resolution of code review comments."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from execution.container_runtime import docker_image_exists
from pipeline.agent_resolver_with_task import AGENT_NAME
from run_agent_resolution_with_task import (
    DEFAULT_DOCKER_IMAGE_MAP_FILE,
    DEFAULT_INTENT_FILE,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QWEN_SETTINGS,
    DEFAULT_TESTGEN_DIR,
    DEFAULT_dataset_FILE,
    load_docker_image_name,
    load_testgen_results,
    process_instance,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_dataset_instances(dataset_file: Path) -> list[dict]:
    """Load all instances from the dataset JSONL file."""
    instances = []
    with dataset_file.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            instances.append(json.loads(line))
    return instances


def load_existing_result(output_dir: Path, instance_id: str) -> dict | None:
    """Load an existing result.json for an instance, or None if not found."""
    slug = instance_id.replace("/", "__")
    result_file = output_dir / slug / "result.json"
    if result_file.exists():
        try:
            return json.loads(result_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load existing result for %s: %s", instance_id, exc)
    return None


def make_skipped_result(instance: dict, *, model: str, error: str) -> dict:
    """Build a result object for instances skipped before processing."""
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "agent": AGENT_NAME,
        "model": model,
        "num_comments": 0,
        "num_resolved": 0,
        "resolution_rate": 0.0,
        "results": [],
        "trajectory": {
            "format": "agent_stdout",
            "path": None,
        },
        "artifacts": {},
        "error": error,
    }


def write_summary(output_dir: Path, all_results: list[dict], elapsed: float) -> dict:
    """Write summary.json with aggregated intent-guided resolution stats."""
    total_comments = sum(result.get("num_comments", 0) for result in all_results)
    total_resolved = sum(result.get("num_resolved", 0) for result in all_results)
    total_errors = sum(1 for result in all_results if result.get("error"))

    repo_data: dict[str, dict] = {}
    for result in all_results:
        repo = result["repo"]
        if repo not in repo_data:
            repo_data[repo] = {
                "repo": repo,
                "instances": 0,
                "comments": 0,
                "resolved": 0,
            }
        repo_row = repo_data[repo]
        repo_row["instances"] += 1
        repo_row["comments"] += result.get("num_comments", 0)
        repo_row["resolved"] += result.get("num_resolved", 0)

    for repo_row in repo_data.values():
        repo_row["resolution_rate"] = (
            repo_row["resolved"] / repo_row["comments"]
            if repo_row["comments"] > 0
            else 0.0
        )

    model = ""
    for result in all_results:
        if result.get("model"):
            model = result["model"]
            break

    summary = {
        "total_instances": len(all_results),
        "total_comments": total_comments,
        "total_resolved": total_resolved,
        "total_errors": total_errors,
        "overall_resolution_rate": (
            total_resolved / total_comments if total_comments > 0 else 0.0
        ),
        "elapsed_seconds": elapsed,
        "model": model,
        "agent": AGENT_NAME,
        "repo_summary": list(repo_data.values()),
        "instance_results": [
            {
                "instance_id": result["instance_id"],
                "repo": result["repo"],
                "num_comments": result.get("num_comments", 0),
                "num_resolved": result.get("num_resolved", 0),
                "resolution_rate": result.get("resolution_rate", 0.0),
                "error": result.get("error"),
            }
            for result in all_results
        ],
    }

    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch intent-guided agent resolution using Qwen Code in Docker"
    )
    parser.add_argument(
        "--dataset-file",
        type=str,
        default=DEFAULT_dataset_FILE,
        help=f"Stage 3 JSONL file (default: {DEFAULT_dataset_FILE})",
    )
    parser.add_argument(
        "--testgen-dir",
        type=str,
        default=DEFAULT_TESTGEN_DIR,
        help=f"Testgen results directory (default: {DEFAULT_TESTGEN_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--intent-file",
        type=str,
        default=DEFAULT_INTENT_FILE,
        help=f"Comment intent JSONL file (default: {DEFAULT_INTENT_FILE})",
    )
    parser.add_argument(
        "--docker-image-map",
        type=str,
        default=DEFAULT_DOCKER_IMAGE_MAP_FILE,
        help=(
            "CSV mapping file with selected Docker images "
            f"(default: {DEFAULT_DOCKER_IMAGE_MAP_FILE})"
        ),
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Qwen model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--qwen-settings",
        "--credentials",
        dest="qwen_settings",
        type=str,
        default=str(DEFAULT_QWEN_SETTINGS),
        help=f"Path to Qwen settings.json (default: {DEFAULT_QWEN_SETTINGS})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Only process instances for this repo",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of instances to process",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-process all instances even if results already exist",
    )
    args = parser.parse_args()

    dataset_file = Path(args.dataset_file)
    testgen_dir = Path(args.testgen_dir)
    output_dir = Path(args.output_dir)
    docker_image_map_file = Path(args.docker_image_map)
    qwen_settings_path = Path(args.qwen_settings)
    intent_file_path = Path(args.intent_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = not args.no_resume

    if not dataset_file.exists():
        logger.error("Stage 3 file not found: %s", dataset_file)
        sys.exit(1)

    if not intent_file_path.exists():
        logger.warning(
            "Intent file not found: %s (all comments use naive fallback)",
            intent_file_path,
        )

    if not docker_image_map_file.exists():
        logger.error("Docker image map file not found: %s", docker_image_map_file)
        sys.exit(1)

    all_dataset = load_dataset_instances(dataset_file)
    logger.info("Loaded %d instances from %s", len(all_dataset), dataset_file)

    if args.repo:
        all_dataset = [instance for instance in all_dataset if instance["repo"] == args.repo]
        logger.info("Filtered to %d instances for repo %s", len(all_dataset), args.repo)

    if args.limit and len(all_dataset) > args.limit:
        all_dataset = all_dataset[:args.limit]
        logger.info("Limited to %d instances", len(all_dataset))

    if not all_dataset:
        logger.error("No instances to process.")
        sys.exit(1)

    all_results: list[dict] = []
    to_process: list[dict] = []

    for instance in all_dataset:
        instance_id = instance["instance_id"]

        if resume:
            existing = load_existing_result(output_dir, instance_id)
            if existing is not None:
                logger.info("Skipping (already done): %s", instance_id)
                all_results.append(existing)
                continue

        docker_image = load_docker_image_name(docker_image_map_file, instance_id)
        if not docker_image or not docker_image_exists(docker_image):
            logger.warning(
                "No Docker image for %s (%s), skipping",
                instance_id,
                docker_image,
            )
            all_results.append(
                make_skipped_result(
                    instance,
                    model=args.model,
                    error=f"Docker image not found: {docker_image}",
                )
            )
            continue

        testgen = load_testgen_results(testgen_dir, instance_id)
        if testgen is None:
            logger.warning("No testgen results for %s, skipping", instance_id)
            all_results.append(
                make_skipped_result(
                    instance,
                    model=args.model,
                    error="No testgen results found",
                )
            )
            continue

        to_process.append(instance)

    if not to_process:
        logger.info("All instances already processed or skipped.")
        summary = write_summary(output_dir, all_results, 0.0)
        logger.info(
            "Summary: %d instances, %d/%d resolved (%.1f%%)",
            summary["total_instances"],
            summary["total_resolved"],
            summary["total_comments"],
            summary["overall_resolution_rate"] * 100,
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

    if not qwen_settings_path.exists():
        logger.warning(
            "Qwen settings file not found: %s (containers may fail to authenticate)",
            qwen_settings_path,
        )

    def _process_one(instance: dict) -> dict:
        instance_id = instance["instance_id"]
        try:
            testgen = load_testgen_results(testgen_dir, instance_id)
            docker_image = load_docker_image_name(docker_image_map_file, instance_id)
            if not docker_image:
                return make_skipped_result(
                    instance,
                    model=args.model,
                    error=f"Docker image not found in map: {docker_image_map_file}",
                )
            return process_instance(
                instance=instance,
                testgen_results=testgen,
                output_dir=output_dir,
                model=args.model,
                docker_image=docker_image,
                qwen_settings_path=qwen_settings_path,
                intent_file_path=intent_file_path,
            )
        except Exception:
            logger.exception("[%s] Error processing instance", instance_id)
            return make_skipped_result(
                instance,
                model=args.model,
                error="Processing failed",
            )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_instance = {
            executor.submit(_process_one, instance): instance
            for instance in to_process
        }

        for future in as_completed(future_to_instance):
            instance = future_to_instance[future]
            result = future.result()

            with lock:
                all_results.append(result)
                processed += 1
                count = processed

            logger.info(
                "[%d/%d] Completed %s: %d/%d resolved",
                count,
                len(to_process),
                instance["instance_id"],
                result.get("num_resolved", 0),
                result.get("num_comments", 0),
            )

            if count % 10 == 0:
                with lock:
                    elapsed_so_far = time.time() - start_time
                    summary = write_summary(output_dir, list(all_results), elapsed_so_far)
                logger.info(
                    "Progress: %d/%d instances, %d/%d resolved (%.1f%%)",
                    len(all_results),
                    len(all_dataset),
                    summary["total_resolved"],
                    summary["total_comments"],
                    summary["overall_resolution_rate"] * 100,
                )

    total_elapsed = time.time() - start_time
    summary = write_summary(output_dir, all_results, total_elapsed)

    logger.info(
        "=== DONE === %d instances, %d/%d resolved (%.1f%%), "
        "%d errors, %.0fs elapsed",
        summary["total_instances"],
        summary["total_resolved"],
        summary["total_comments"],
        summary["overall_resolution_rate"] * 100,
        summary["total_errors"],
        total_elapsed,
    )
    logger.info("Summary: %s", output_dir / "summary.json")


if __name__ == "__main__":
    main()
