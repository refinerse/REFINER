#!/usr/bin/env python3
"""Validate verified acceptance tests against the ground-truth merged patch.

For each instance this script checks the fail-to-pass property of every
verified generated test:

1. Locate verified generated tests in testgen_combined/<instance_id>/result.json
2. Start the corresponding Docker image
3. Reset the repo to commit_to_review.head_commit and run each test
   (expectation: the test FAILS, because the fix is not present yet)
4. Check out the dataset's ground-truth ``merged_commit`` and run each test
   again (expectation: the test PASSES, because the fix is now present).
   This is the faithful merged state; the ``merged_patch`` field is a diff
   against ``base_commit`` and does not git-apply onto ``head_commit``.
5. A test is "valid" when it fails on head AND passes on merged.

Usage:
  python run_batch_gt_validation.py --workers 30
  python run_batch_gt_validation.py --repo tobymao/sqlglot --limit 5
  python run_batch_gt_validation.py --no-resume
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline.agent_resolver import verify_with_test

# Reuse the building blocks from the patch-replay script.
from run_batch_patch_verification import (
    ensure_git_safe_directory,
    load_combined_result,
    load_dataset_instances,
    load_existing_result,
    reinstall_python_repo,
    verified_tests_from_result,
    write_instance_result,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_DATASET_FILE = "dataset/instances.jsonl"
DEFAULT_TESTGEN_DIR = "testgen_combined"
DEFAULT_OUTPUT_DIR = "results_gt_validation"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"


def load_docker_image_map(docker_image_map_file: Path) -> dict[str, str]:
    """Load precomputed, locally-available images from the instance/image CSV.

    Using the CSV's ``selected_image`` avoids live Docker probing that could
    otherwise fall through to a registry pull.
    """
    if not docker_image_map_file.exists():
        raise FileNotFoundError(f"Docker image map file not found: {docker_image_map_file}")

    mapping: dict[str, str] = {}
    with docker_image_map_file.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            instance_id = (row.get("instance_id") or "").strip()
            selected_image = (row.get("selected_image") or "").strip()
            if instance_id and selected_image:
                mapping[instance_id] = selected_image
    return mapping


def make_stub_result(instance: dict, *, error: str, results: list[dict] | None = None) -> dict:
    """Create a standard failure/skip result payload."""
    test_results = results or []
    num_tests = len(test_results)
    num_valid = sum(1 for r in test_results if r.get("valid"))
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "merged_patch_applied": False,
        "merged_patch_apply_output": "",
        "num_tests": num_tests,
        "num_valid": num_valid,
        "valid_rate": (num_valid / num_tests) if num_tests else 0.0,
        "results": test_results,
        "error": error,
    }


def process_instance(
    instance: dict,
    testgen_result: dict,
    output_dir: Path,
    docker_image: str,
) -> dict:
    """Run the fail-on-head / pass-on-merged check for one instance."""
    instance_id = instance["instance_id"]
    verified_tests = verified_tests_from_result(instance, testgen_result)
    if not verified_tests:
        result = make_stub_result(instance, error="No successful generated tests found")
        write_instance_result(output_dir, result)
        return result

    has_python = any(t["language"] == "python" for t in verified_tests)

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-gtvalid-{safe_name}"

    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True)

    session = DockerContainerSession(docker_image, name=container_name)
    merged_patch_applied = False
    merged_patch_apply_output = ""
    # comment_index -> partial result row
    rows: dict[int, dict] = {
        t["comment_index"]: {
            "comment_index": t["comment_index"],
            "comment_text": t["comment_text"],
            "comment_type": t["comment_type"],
            "language": t["language"],
            "test_file": t["test_file"],
            "passed_on_head": None,
            "passed_on_merged": None,
            "valid": False,
            "head_output": "",
            "merged_output": "",
            "error": None,
        }
        for t in verified_tests
    }

    try:
        session.start()
        ensure_git_safe_directory(session)

        head_commit = instance["commit_to_review"]["head_commit"]
        reset_result = session.run_command(
            f"git checkout --force {head_commit} && git clean -fd --quiet",
            timeout=120,
        )
        if reset_result.returncode != 0:
            error_message = f"git checkout head failed: {reset_result.stderr[:500]}"
            for row in rows.values():
                row["error"] = error_message
            result = make_stub_result(instance, error=error_message, results=list(rows.values()))
            write_instance_result(output_dir, result)
            return result

        # --- Stage 1: run each test on the unfixed head commit (expect FAIL) ---
        if has_python:
            reinstall_python_repo(session)

        for test in verified_tests:
            passed, output = verify_with_test(
                session=session,
                test_code=test["test_code"],
                test_filename=test["test_file"],
                language=test["language"],
            )
            row = rows[test["comment_index"]]
            row["passed_on_head"] = passed
            row["head_output"] = output

        # --- Stage 2: check out the ground-truth merged commit (expect tests PASS) ---
        merged_commit = instance["merged_commit"]
        merged_reset = session.run_command(
            f"git checkout --force {merged_commit} && git clean -fd --quiet",
            timeout=120,
        )
        merged_patch_apply_output = (merged_reset.stdout + "\n" + merged_reset.stderr).strip()
        if merged_reset.returncode != 0:
            error_message = f"git checkout merged failed: {merged_reset.stderr[:500]}"
            for row in rows.values():
                row["error"] = error_message
            result = make_stub_result(instance, error=error_message, results=list(rows.values()))
            result["merged_patch_apply_output"] = merged_patch_apply_output
            write_instance_result(output_dir, result)
            return result
        merged_patch_applied = True

        if has_python:
            reinstall_python_repo(session)

        for test in verified_tests:
            passed, output = verify_with_test(
                session=session,
                test_code=test["test_code"],
                test_filename=test["test_file"],
                language=test["language"],
            )
            row = rows[test["comment_index"]]
            row["passed_on_merged"] = passed
            row["merged_output"] = output
            row["valid"] = bool(row["passed_on_head"] is False and passed)

    except Exception as exc:
        logger.exception("[%s] Error during gt validation", instance_id)
        error_message = str(exc)
        for row in rows.values():
            if row["error"] is None:
                row["error"] = error_message
        result = make_stub_result(instance, error=error_message, results=list(rows.values()))
        result["merged_patch_applied"] = merged_patch_applied
        result["merged_patch_apply_output"] = merged_patch_apply_output
        write_instance_result(output_dir, result)
        return result
    finally:
        session.remove(force=True)

    test_results = list(rows.values())
    num_tests = len(test_results)
    num_valid = sum(1 for r in test_results if r["valid"])
    result = {
        "instance_id": instance_id,
        "repo": instance["repo"],
        "merged_patch_applied": True,
        "merged_patch_apply_output": merged_patch_apply_output,
        "num_tests": num_tests,
        "num_valid": num_valid,
        "valid_rate": (num_valid / num_tests) if num_tests else 0.0,
        "results": test_results,
        "error": None,
    }
    write_instance_result(output_dir, result)
    return result


def write_summary(output_dir: Path, all_results: list[dict], elapsed: float) -> dict:
    """Write summary.json with aggregate gt-validation stats."""
    total_tests = sum(r.get("num_tests", 0) for r in all_results)
    total_valid = sum(r.get("num_valid", 0) for r in all_results)
    total_errors = sum(1 for r in all_results if r.get("error"))

    repo_summary: dict[str, dict] = {}
    for result in all_results:
        repo = result["repo"]
        data = repo_summary.setdefault(
            repo, {"repo": repo, "instances": 0, "tests": 0, "valid": 0}
        )
        data["instances"] += 1
        data["tests"] += result.get("num_tests", 0)
        data["valid"] += result.get("num_valid", 0)

    for data in repo_summary.values():
        data["valid_rate"] = (data["valid"] / data["tests"]) if data["tests"] else 0.0

    summary = {
        "total_instances": len(all_results),
        "total_tests": total_tests,
        "total_valid": total_valid,
        "total_errors": total_errors,
        "overall_valid_rate": (total_valid / total_tests) if total_tests else 0.0,
        "elapsed_seconds": elapsed,
        "repo_summary": list(repo_summary.values()),
        "instance_results": [
            {
                "instance_id": r["instance_id"],
                "repo": r["repo"],
                "merged_patch_applied": r.get("merged_patch_applied", False),
                "num_tests": r.get("num_tests", 0),
                "num_valid": r.get("num_valid", 0),
                "valid_rate": r.get("valid_rate", 0.0),
                "error": r.get("error"),
            }
            for r in all_results
        ],
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate verified acceptance tests against the ground-truth merged patch"
    )
    parser.add_argument("--dataset-file", type=str, default=DEFAULT_DATASET_FILE)
    parser.add_argument("--testgen-dir", type=str, default=DEFAULT_TESTGEN_DIR)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--docker-image-map-file",
        type=str,
        default=DEFAULT_DOCKER_IMAGE_MAP_FILE,
        help=f"CSV mapping instance_id -> selected_image (default: {DEFAULT_DOCKER_IMAGE_MAP_FILE})",
    )
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")

    args = parser.parse_args()

    dataset_file = Path(args.dataset_file)
    testgen_dir = Path(args.testgen_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = not args.no_resume

    if not dataset_file.exists():
        logger.error("Dataset file not found: %s", dataset_file)
        sys.exit(1)

    docker_image_map = load_docker_image_map(Path(args.docker_image_map_file))
    logger.info(
        "Loaded %d image mappings from %s", len(docker_image_map), args.docker_image_map_file
    )

    all_dataset = load_dataset_instances(dataset_file)
    logger.info("Loaded %d instances from %s", len(all_dataset), dataset_file)

    if args.repo:
        all_dataset = [i for i in all_dataset if i["repo"] == args.repo]
        logger.info("Filtered to %d instances for repo %s", len(all_dataset), args.repo)

    if args.limit and len(all_dataset) > args.limit:
        all_dataset = all_dataset[: args.limit]
        logger.info("Limited to %d instances", len(all_dataset))

    if not all_dataset:
        logger.error("No instances to process.")
        sys.exit(1)

    all_results: list[dict] = []
    to_process: list[tuple[dict, dict, str]] = []

    for instance in all_dataset:
        instance_id = instance["instance_id"]

        if resume:
            existing = load_existing_result(output_dir, instance_id)
            if existing is not None:
                logger.info("Skipping (already done): %s", instance_id)
                all_results.append(existing)
                continue

        testgen_result = load_combined_result(testgen_dir, instance_id)
        if testgen_result is None:
            all_results.append(make_stub_result(instance, error="No combined testgen result found"))
            continue

        if not instance.get("merged_commit", "").strip():
            all_results.append(make_stub_result(instance, error="Empty merged_commit in dataset"))
            continue

        docker_image = docker_image_map.get(instance_id)
        if not docker_image:
            all_results.append(
                make_stub_result(instance, error="No selected_image in docker image map")
            )
            continue

        to_process.append((instance, testgen_result, docker_image))

    if not to_process:
        summary = write_summary(output_dir, all_results, 0.0)
        logger.info(
            "Summary: %d instances, %d/%d tests valid (%.1f%%)",
            summary["total_instances"],
            summary["total_valid"],
            summary["total_tests"],
            summary["overall_valid_rate"] * 100,
        )
        return

    start_time = time.time()
    processed = 0
    lock = threading.Lock()

    logger.info("Processing %d instance(s) with %d worker(s)", len(to_process), args.workers)

    def _process_one(instance, testgen_result, docker_image) -> dict:
        return process_instance(
            instance=instance,
            testgen_result=testgen_result,
            output_dir=output_dir,
            docker_image=docker_image,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_instance = {
            executor.submit(_process_one, instance, testgen_result, docker_image): instance
            for instance, testgen_result, docker_image in to_process
        }

        for future in as_completed(future_to_instance):
            instance = future_to_instance[future]
            try:
                result = future.result()
            except Exception:
                logger.exception("[%s] Unexpected batch processing failure", instance["instance_id"])
                result = make_stub_result(instance, error="Processing failed")
                write_instance_result(output_dir, result)

            with lock:
                all_results.append(result)
                processed += 1
                count = processed

            logger.info(
                "[%d/%d] %s: %d/%d tests valid (fail@head & pass@merged)",
                count,
                len(to_process),
                instance["instance_id"],
                result.get("num_valid", 0),
                result.get("num_tests", 0),
            )

            if count % 10 == 0:
                with lock:
                    summary = write_summary(output_dir, list(all_results), time.time() - start_time)
                logger.info(
                    "Progress: %d/%d instances, %d/%d tests valid (%.1f%%)",
                    len(all_results),
                    len(all_dataset),
                    summary["total_valid"],
                    summary["total_tests"],
                    summary["overall_valid_rate"] * 100,
                )

    total_elapsed = time.time() - start_time
    summary = write_summary(output_dir, all_results, total_elapsed)
    logger.info(
        "=== DONE === %d instances, %d/%d tests valid (%.1f%%), %d errors, %.0fs elapsed",
        summary["total_instances"],
        summary["total_valid"],
        summary["total_tests"],
        summary["overall_valid_rate"] * 100,
        summary["total_errors"],
        total_elapsed,
    )
    logger.info("Summary: %s", output_dir / "summary.json")


if __name__ == "__main__":
    main()
