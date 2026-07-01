#!/usr/bin/env python3
"""Validate the *split* acceptance tests and report per-assertion pass counts.

This is the sibling of ``run_batch_gt_validation.py`` for the
``testgen_combined_splitted`` tree produced by ``split_acceptance_tests.py``.

Two differences from the original validator:

1. **No ``-x``.** Each split file now holds one function per assertion, so we
   run pytest *without* fail-fast and parse pytest's own summary line. That
   yields the parsable numbers the split was made for: how many of a file's
   checks pass / fail / error on each commit.

2. **Per-assertion fields** are recorded per comment:
   ``num_assertions`` (functions collected), ``head_passed`` / ``head_failed``,
   ``merged_passed`` / ``merged_failed``.

Validity is unchanged in spirit: a test is **valid** when it fails on
``head_commit`` (>=1 assertion fails/errors -> non-zero pytest exit) and passes
on ``merged_commit`` (every assertion passes).

Usage:
  python run_batch_gt_validation_splitted.py --workers 30
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline.agent_resolver import verify_with_test
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
DEFAULT_TESTGEN_DIR = "results_testgen_splitted"
DEFAULT_OUTPUT_DIR = "results_gt_validation_splitted"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"

# Parse pytest summary tokens like "3 passed", "1 failed", "2 errors".
_SUMMARY_RE = re.compile(r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed)")


def parse_pytest_counts(output: str) -> dict[str, int]:
    """Extract counts from the last pytest summary line in ``output``."""
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    # Scan the final non-empty lines for the summary; take all matches found.
    for line in reversed(output.splitlines()):
        matches = _SUMMARY_RE.findall(line)
        if not matches:
            continue
        for num, kind in matches:
            key = "error" if kind in ("error", "errors") else kind
            if key in counts:
                counts[key] += int(num)
            elif key in ("xfailed", "xpassed"):
                # Treat xfail as not-passed; ignore for our purposes.
                pass
        break
    return counts


def run_split_test(
    session: DockerContainerSession,
    test_code: str,
    test_filename: str,
) -> dict:
    """Run one (already-split) python test file WITHOUT -x; return counts."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f"_{test_filename}", delete=False
    ) as f:
        f.write(test_code)
        local_test_path = Path(f.name)
    try:
        container_test_path = f"/workspace/{test_filename}"
        session.copy_to(local_test_path, container_test_path)
    finally:
        local_test_path.unlink(missing_ok=True)

    run_cmd = (
        f"python -m pytest {container_test_path} -v --tb=line --no-header "
        f"-c /dev/null -p no:cacheprovider"
    )
    result = session.run_command(run_cmd, timeout=120)
    combined = (result.stdout + "\n" + result.stderr).strip()
    counts = parse_pytest_counts(combined)
    total = counts["passed"] + counts["failed"] + counts["error"]
    return {
        "passed_all": result.returncode == 0,
        "num_assertions": total,
        "passed": counts["passed"],
        "failed": counts["failed"] + counts["error"],
        "output": combined,
    }


def _run_one(session: DockerContainerSession, test: dict) -> dict:
    """Run one verified test. Python files are split (per-assertion counts);
    other languages run unsplit via the standard single pass/fail runner."""
    if test["language"] == "python":
        return run_split_test(session, test["test_code"], test["test_file"])
    passed, output = verify_with_test(
        session=session,
        test_code=test["test_code"],
        test_filename=test["test_file"],
        language=test["language"],
    )
    return {
        "passed_all": passed,
        "num_assertions": 1,
        "passed": 1 if passed else 0,
        "failed": 0 if passed else 1,
        "output": output,
    }


def load_docker_image_map(docker_image_map_file: Path) -> dict[str, str]:
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
    instance_id = instance["instance_id"]
    verified_tests = verified_tests_from_result(instance, testgen_result)
    if not verified_tests:
        result = make_stub_result(instance, error="No successful generated tests found")
        write_instance_result(output_dir, result)
        return result

    # Only python tests are executable here (jest/go handled elsewhere).
    has_python = any(t["language"] == "python" for t in verified_tests)

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-gtsplit-{safe_name}"
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True)

    session = DockerContainerSession(docker_image, name=container_name)
    merged_patch_apply_output = ""
    rows: dict[int, dict] = {
        t["comment_index"]: {
            "comment_index": t["comment_index"],
            "comment_text": t["comment_text"],
            "comment_type": t["comment_type"],
            "language": t["language"],
            "test_file": t["test_file"],
            "num_assertions": None,
            "head_passed": None,
            "head_failed": None,
            "merged_passed": None,
            "merged_failed": None,
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
            f"git checkout --force {head_commit} && git clean -fd --quiet", timeout=120
        )
        if reset_result.returncode != 0:
            error_message = f"git checkout head failed: {reset_result.stderr[:500]}"
            for row in rows.values():
                row["error"] = error_message
            result = make_stub_result(instance, error=error_message, results=list(rows.values()))
            write_instance_result(output_dir, result)
            return result

        # --- Stage 1: head commit (expect at least one assertion FAILS) ---
        if has_python:
            reinstall_python_repo(session)
        for test in verified_tests:
            info = _run_one(session, test)
            row = rows[test["comment_index"]]
            row["num_assertions"] = info["num_assertions"]
            row["head_passed"] = info["passed"]
            row["head_failed"] = info["failed"]
            row["passed_on_head"] = info["passed_all"]
            row["head_output"] = info["output"]

        # --- Stage 2: merged commit (expect ALL assertions PASS) ---
        merged_commit = instance["merged_commit"]
        merged_reset = session.run_command(
            f"git checkout --force {merged_commit} && git clean -fd --quiet", timeout=120
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

        if has_python:
            reinstall_python_repo(session)
        for test in verified_tests:
            info = _run_one(session, test)
            row = rows[test["comment_index"]]
            row["merged_passed"] = info["passed"]
            row["merged_failed"] = info["failed"]
            row["passed_on_merged"] = info["passed_all"]
            row["merged_output"] = info["output"]
            row["valid"] = bool(row["passed_on_head"] is False and info["passed_all"])

    except Exception as exc:
        logger.exception("[%s] Error during gt validation", instance_id)
        error_message = str(exc)
        for row in rows.values():
            if row["error"] is None:
                row["error"] = error_message
        result = make_stub_result(instance, error=error_message, results=list(rows.values()))
        result["merged_patch_apply_output"] = merged_patch_apply_output
        write_instance_result(output_dir, result)
        return result
    finally:
        session.remove(force=True)

    test_results = list(rows.values())
    num_tests = len(test_results)
    num_valid = sum(1 for r in test_results if r["valid"])
    # Aggregate assertion-level tallies for this instance.
    total_assertions = sum((r["num_assertions"] or 0) for r in test_results)
    merged_assertions_passed = sum((r["merged_passed"] or 0) for r in test_results)
    result = {
        "instance_id": instance_id,
        "repo": instance["repo"],
        "merged_patch_applied": True,
        "merged_patch_apply_output": merged_patch_apply_output,
        "num_tests": num_tests,
        "num_valid": num_valid,
        "valid_rate": (num_valid / num_tests) if num_tests else 0.0,
        "total_assertions": total_assertions,
        "merged_assertions_passed": merged_assertions_passed,
        "results": test_results,
        "error": None,
    }
    write_instance_result(output_dir, result)
    return result


def write_summary(output_dir: Path, all_results: list[dict], elapsed: float) -> dict:
    total_tests = sum(r.get("num_tests", 0) for r in all_results)
    total_valid = sum(r.get("num_valid", 0) for r in all_results)
    total_errors = sum(1 for r in all_results if r.get("error"))
    total_assertions = sum(r.get("total_assertions", 0) for r in all_results)
    merged_assertions_passed = sum(r.get("merged_assertions_passed", 0) for r in all_results)

    summary = {
        "total_instances": len(all_results),
        "total_tests": total_tests,
        "total_valid": total_valid,
        "total_errors": total_errors,
        "overall_valid_rate": (total_valid / total_tests) if total_tests else 0.0,
        "total_assertions": total_assertions,
        "merged_assertions_passed": merged_assertions_passed,
        "merged_assertion_pass_rate": (
            merged_assertions_passed / total_assertions if total_assertions else 0.0
        ),
        "elapsed_seconds": elapsed,
        "instance_results": [
            {
                "instance_id": r["instance_id"],
                "repo": r["repo"],
                "num_tests": r.get("num_tests", 0),
                "num_valid": r.get("num_valid", 0),
                "total_assertions": r.get("total_assertions", 0),
                "merged_assertions_passed": r.get("merged_assertions_passed", 0),
                "error": r.get("error"),
            }
            for r in all_results
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate split acceptance tests")
    parser.add_argument("--dataset-file", type=str, default=DEFAULT_DATASET_FILE)
    parser.add_argument("--testgen-dir", type=str, default=DEFAULT_TESTGEN_DIR)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--docker-image-map-file", type=str, default=DEFAULT_DOCKER_IMAGE_MAP_FILE)
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only-file", type=str, default=None,
                        help="Path to a newline-separated list of instance_ids to run")
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
    all_dataset = load_dataset_instances(dataset_file)
    logger.info("Loaded %d instances", len(all_dataset))

    if args.repo:
        all_dataset = [i for i in all_dataset if i["repo"] == args.repo]
    if args.only_file:
        wanted = {
            line.strip()
            for line in Path(args.only_file).read_text().splitlines()
            if line.strip()
        }
        all_dataset = [i for i in all_dataset if i["instance_id"] in wanted]
        logger.info("Filtered to %d instances from %s", len(all_dataset), args.only_file)
    if args.limit and len(all_dataset) > args.limit:
        all_dataset = all_dataset[: args.limit]

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
            all_results.append(make_stub_result(instance, error="No selected_image in docker image map"))
            continue
        to_process.append((instance, testgen_result, docker_image))

    if not to_process:
        summary = write_summary(output_dir, all_results, 0.0)
        logger.info("Nothing to run. %d/%d tests valid", summary["total_valid"], summary["total_tests"])
        return

    start_time = time.time()
    processed = 0
    lock = threading.Lock()
    logger.info("Processing %d instance(s) with %d worker(s)", len(to_process), args.workers)

    def _process_one(instance, testgen_result, docker_image) -> dict:
        return process_instance(
            instance=instance, testgen_result=testgen_result,
            output_dir=output_dir, docker_image=docker_image,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_instance = {
            executor.submit(_process_one, inst, tr, img): inst
            for inst, tr, img in to_process
        }
        for future in as_completed(future_to_instance):
            instance = future_to_instance[future]
            try:
                result = future.result()
            except Exception:
                logger.exception("[%s] batch failure", instance["instance_id"])
                result = make_stub_result(instance, error="Processing failed")
                write_instance_result(output_dir, result)
            with lock:
                all_results.append(result)
                processed += 1
                count = processed
            logger.info(
                "[%d/%d] %s: %d/%d tests valid, %d/%d assertions pass on merged",
                count, len(to_process), instance["instance_id"],
                result.get("num_valid", 0), result.get("num_tests", 0),
                result.get("merged_assertions_passed", 0), result.get("total_assertions", 0),
            )
            if count % 10 == 0:
                with lock:
                    write_summary(output_dir, list(all_results), time.time() - start_time)

    total_elapsed = time.time() - start_time
    summary = write_summary(output_dir, all_results, total_elapsed)
    logger.info(
        "=== DONE === %d inst, %d/%d tests valid (%.1f%%), %d/%d assertions pass on merged, %d errors, %.0fs",
        summary["total_instances"], summary["total_valid"], summary["total_tests"],
        summary["overall_valid_rate"] * 100,
        summary["merged_assertions_passed"], summary["total_assertions"],
        summary["total_errors"], total_elapsed,
    )


if __name__ == "__main__":
    main()
