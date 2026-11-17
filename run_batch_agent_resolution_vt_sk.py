#!/usr/bin/env python3
"""Batch validation-test and intent guided agent resolution."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from execution.container_runtime import docker_image_exists
from pipeline.agent_resolver_vt_sk import AGENT_NAME
from pipeline.agent_resolver_with_task import DEFAULT_INTENT_FILE
from run_agent_resolution_vt_sk import DEFAULT_OUTPUT_DIR, process_instance
from run_agent_resolution_validation_test import (
    DEFAULT_DATASET_FILE,
    DEFAULT_DOCKER_IMAGE_MAP_FILE,
    DEFAULT_MODEL,
    DEFAULT_QWEN_SETTINGS,
    DEFAULT_TESTGEN_DIR,
    DEFAULT_VALIDATION_TEST_DIR,
    load_testgen_results,
    load_validation_result,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def instance_slug(instance_id: str) -> str:
    return instance_id.replace("/", "__")


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
    """Load an existing result.json for an instance, or None."""
    result_file = output_dir / instance_slug(instance_id) / "result.json"
    if not result_file.exists():
        return None
    try:
        return json.loads(result_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load existing result for %s: %s", instance_id, exc)
        return None


def load_docker_image_map(docker_image_map_file: Path) -> dict[str, str]:
    """Load selected Docker images keyed by instance ID."""
    if not docker_image_map_file.exists():
        raise FileNotFoundError(
            f"Docker image map file not found: {docker_image_map_file}"
        )

    image_map: dict[str, str] = {}
    with docker_image_map_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            instance_id = (row.get("instance_id") or "").strip()
            selected_image = (row.get("selected_image") or "").strip()
            if instance_id and selected_image:
                image_map[instance_id] = selected_image
    return image_map


def make_skipped_result(
    instance: dict,
    *,
    model: str,
    intent_file_path: Path,
    error: str,
) -> dict:
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "agent": AGENT_NAME,
        "model": model,
        "intent_file": str(intent_file_path),
        "intent_by_comment_index": {},
        "num_comments": 0,
        "num_resolved": 0,
        "resolution_rate": 0.0,
        "num_expected_failures_observed": 0,
        "num_initial_unexpected_passes": 0,
        "num_validation_tests_revised": 0,
        "results": [],
        "groundtruth_assessment": {
            "num_tests": 0,
            "num_passed": 0,
            "pass_rate": None,
            "results": [],
        },
        "trajectory": {
            "format": "agent_stdout",
            "path": None,
        },
        "artifacts": {},
        "error": error,
    }


def write_summary(output_dir: Path, all_results: list[dict], elapsed: float) -> dict:
    """Write summary.json with aggregate VT+intent repair and assessment stats."""
    total_comments = sum(result.get("num_comments", 0) for result in all_results)
    total_resolved = sum(result.get("num_resolved", 0) for result in all_results)
    total_errors = sum(1 for result in all_results if result.get("error"))
    total_expected_failures = sum(
        result.get("num_expected_failures_observed", 0) for result in all_results
    )
    total_initial_unexpected_passes = sum(
        result.get("num_initial_unexpected_passes", 0) for result in all_results
    )
    total_validation_tests_revised = sum(
        result.get("num_validation_tests_revised", 0) for result in all_results
    )
    total_gt_tests = sum(
        (result.get("groundtruth_assessment") or {}).get("num_tests", 0)
        for result in all_results
    )
    total_gt_passed = sum(
        (result.get("groundtruth_assessment") or {}).get("num_passed", 0)
        for result in all_results
    )

    repo_data: dict[str, dict] = {}
    for result in all_results:
        repo = result["repo"]
        if repo not in repo_data:
            repo_data[repo] = {
                "repo": repo,
                "instances": 0,
                "comments": 0,
                "resolved": 0,
                "expected_failures_observed": 0,
                "initial_unexpected_passes": 0,
                "validation_tests_revised": 0,
                "gt_tests": 0,
                "gt_passed": 0,
            }
        row = repo_data[repo]
        groundtruth = result.get("groundtruth_assessment") or {}
        row["instances"] += 1
        row["comments"] += result.get("num_comments", 0)
        row["resolved"] += groundtruth.get("num_passed", 0)
        row["expected_failures_observed"] += result.get(
            "num_expected_failures_observed",
            0,
        )
        row["initial_unexpected_passes"] += result.get(
            "num_initial_unexpected_passes",
            0,
        )
        row["validation_tests_revised"] += result.get(
            "num_validation_tests_revised",
            0,
        )
        row["gt_tests"] += groundtruth.get("num_tests", 0)
        row["gt_passed"] += groundtruth.get("num_passed", 0)

    for row in repo_data.values():
        row["resolution_rate"] = (
            row["gt_passed"] / row["gt_tests"] if row["gt_tests"] else None
        )
        row["gt_pass_rate"] = row["resolution_rate"]

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
        "total_expected_failures_observed": total_expected_failures,
        "total_initial_unexpected_passes": total_initial_unexpected_passes,
        "total_validation_tests_revised": total_validation_tests_revised,
        "overall_resolution_rate": (
            total_gt_passed / total_gt_tests if total_gt_tests else None
        ),
        "groundtruth_assessment": {
            "total_tests": total_gt_tests,
            "total_passed": total_gt_passed,
            "pass_rate": total_gt_passed / total_gt_tests if total_gt_tests else None,
        },
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
                "num_expected_failures_observed": result.get(
                    "num_expected_failures_observed",
                    0,
                ),
                "num_initial_unexpected_passes": result.get(
                    "num_initial_unexpected_passes",
                    0,
                ),
                "num_validation_tests_revised": result.get(
                    "num_validation_tests_revised",
                    0,
                ),
                "groundtruth_assessment": result.get("groundtruth_assessment"),
                "error": result.get("error"),
            }
            for result in all_results
        ],
    }
    summary_file = output_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def _format_rate(rate: float | None) -> float:
    return rate * 100 if rate is not None else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch validation-test and intent guided agent resolution"
    )
    parser.add_argument(
        "--dataset-file",
        type=str,
        default=DEFAULT_DATASET_FILE,
        help=f"Dataset JSONL file (default: {DEFAULT_DATASET_FILE})",
    )
    parser.add_argument(
        "--validation-test-dir",
        dest="validation_test_dir",
        type=str,
        default=DEFAULT_VALIDATION_TEST_DIR,
        help=(
            "Generated validation-test results directory "
            f"(default: {DEFAULT_VALIDATION_TEST_DIR})"
        ),
    )
    parser.add_argument(
        "--testgen-dir",
        dest="testgen_dir",
        type=str,
        default=DEFAULT_TESTGEN_DIR,
        help=(
            "Groundtruth testgen_combined directory used for assessment "
            f"(default: {DEFAULT_TESTGEN_DIR})"
        ),
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
        "--docker-image-map",
        type=str,
        default=DEFAULT_DOCKER_IMAGE_MAP_FILE,
        help=(
            "CSV mapping file with selected Docker images "
            f"(default: {DEFAULT_DOCKER_IMAGE_MAP_FILE})"
        ),
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-process all instances even if results already exist",
    )
    args = parser.parse_args()

    dataset_file = Path(args.dataset_file)
    validation_test_dir = Path(args.validation_test_dir)
    testgen_dir = Path(args.testgen_dir)
    output_dir = Path(args.output_dir)
    qwen_settings_path = Path(args.qwen_settings)
    docker_image_map_file = Path(args.docker_image_map)
    intent_file_path = Path(args.intent_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = not args.no_resume

    if not dataset_file.exists():
        logger.error("Dataset file not found: %s", dataset_file)
        sys.exit(1)
    if not validation_test_dir.exists():
        logger.error("Validation-test directory not found: %s", validation_test_dir)
        sys.exit(1)
    if not intent_file_path.exists():
        logger.warning(
            "Intent file not found: %s (all comments use naive-intent fallback)",
            intent_file_path,
        )
    try:
        docker_image_map = load_docker_image_map(docker_image_map_file)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)

    all_dataset = load_dataset_instances(dataset_file)
    logger.info("Loaded %d instances from %s", len(all_dataset), dataset_file)

    if args.repo:
        all_dataset = [
            instance for instance in all_dataset if instance["repo"] == args.repo
        ]
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

        docker_image = docker_image_map.get(instance_id)
        if not docker_image:
            logger.warning(
                "No Docker image mapping for %s in %s, skipping",
                instance_id,
                docker_image_map_file,
            )
            all_results.append(
                make_skipped_result(
                    instance,
                    model=args.model,
                    intent_file_path=intent_file_path,
                    error=f"Docker image mapping not found in {docker_image_map_file}",
                )
            )
            continue
        if not docker_image_exists(docker_image):
            logger.warning("No Docker image for %s (%s), skipping", instance_id, docker_image)
            all_results.append(
                make_skipped_result(
                    instance,
                    model=args.model,
                    intent_file_path=intent_file_path,
                    error=f"Docker image not found: {docker_image}",
                )
            )
            continue

        validation_result = load_validation_result(validation_test_dir, instance_id)
        if validation_result is None:
            logger.warning(
                "No validation-test results for %s; Qwen will be asked to create tests",
                instance_id,
            )

        to_process.append(instance)

    if not to_process:
        logger.info("All instances already processed or skipped.")
        summary = write_summary(output_dir, all_results, 0.0)
        logger.info(
            "Summary: %d instances, %d/%d resolved (%.1f%%)",
            summary["total_instances"],
            summary["total_resolved"],
            summary["total_comments"],
            _format_rate(summary["overall_resolution_rate"]),
        )
        return

    if not qwen_settings_path.exists():
        logger.warning(
            "Qwen settings file not found: %s (containers may fail to authenticate)",
            qwen_settings_path,
        )

    start_time = time.time()
    processed = 0
    lock = threading.Lock()

    logger.info(
        "Processing %d instance(s) with %d worker(s)",
        len(to_process),
        args.workers,
    )

    def _process_one(instance: dict) -> dict:
        instance_id = instance["instance_id"]
        try:
            validation_result = load_validation_result(validation_test_dir, instance_id)
            testgen_results = load_testgen_results(testgen_dir, instance_id)
            if testgen_results is None:
                logger.warning(
                    "No groundtruth testgen results for %s; assessment will be skipped",
                    instance_id,
                )
            docker_image = docker_image_map[instance_id]
            return process_instance(
                instance=instance,
                validation_result=validation_result,
                validation_test_dir=validation_test_dir,
                testgen_results=testgen_results,
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
                intent_file_path=intent_file_path,
                error="Processing failed",
            )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_instance = {
            executor.submit(_process_one, instance): instance for instance in to_process
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
                    _format_rate(summary["overall_resolution_rate"]),
                )

    total_elapsed = time.time() - start_time
    summary = write_summary(output_dir, all_results, total_elapsed)
    logger.info(
        "=== DONE === %d instances, %d/%d resolved (%.1f%%), "
        "%d revised validation tests, %d errors, %.0fs elapsed",
        summary["total_instances"],
        summary["total_resolved"],
        summary["total_comments"],
        _format_rate(summary["overall_resolution_rate"]),
        summary["total_validation_tests_revised"],
        summary["total_errors"],
        total_elapsed,
    )
    logger.info("Summary: %s", output_dir / "summary.json")


if __name__ == "__main__":
    main()
