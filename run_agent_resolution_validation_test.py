#!/usr/bin/env python3
"""Per-instance validation-test guided agent resolution with Qwen Code."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline.agent_resolver import (
    get_qwen_auth_config,
    get_qwen_mounts,
    setup_qwen_in_container,
    verify_with_test_details,
)
from pipeline.agent_resolver_validation_test import (
    resolve_instance_with_validation_tests,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = ""
DEFAULT_VALIDATION_TEST_DIR = "agents_results/results_testgen_qwen_3.6_plus"
DEFAULT_TESTGEN_DIR = "testgen_combined"
DEFAULT_DATASET_FILE = "dataset/instances.jsonl"
DEFAULT_OUTPUT_DIR = "results_agent_resolution_validation_test"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"
DEFAULT_QWEN_SETTINGS = Path.home() / ".qwen" / "settings.json"

LANGUAGE_EXTENSIONS = {
    "python": ".py",
    "javascript": ".test.js",
    "typescript": ".test.ts",
    "go": "_test.go",
}


def instance_slug(instance_id: str) -> str:
    return instance_id.replace("/", "__")


def load_dataset_instance(dataset_file: Path, instance_id: str) -> dict | None:
    """Load a single instance from the dataset JSONL file."""
    with dataset_file.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            instance = json.loads(line)
            if instance["instance_id"] == instance_id:
                return instance
    return None


def load_validation_result(validation_test_dir: Path, instance_id: str) -> dict | None:
    """Load generated validation-test result.json for an instance."""
    result_file = validation_test_dir / instance_slug(instance_id) / "result.json"
    if not result_file.exists():
        return None
    return json.loads(result_file.read_text(encoding="utf-8"))


def load_testgen_results(testgen_dir: Path, instance_id: str) -> dict | None:
    """Load groundtruth testgen result.json for an instance (testgen_combined)."""
    slug = instance_slug(instance_id)
    result_file = testgen_dir / slug / "result.json"
    if not result_file.exists():
        return None
    return json.loads(result_file.read_text(encoding="utf-8"))


def match_tests_to_comments(
    comments: list[dict], testgen_result: dict
) -> dict[int, tuple[dict, str, str]]:
    """Match Stage 3 comments to their verified test code.

    Returns dict mapping comment index -> (comment_dict, test_code, test_filename).
    Only includes comments that had successful tests in Stage 3.
    """
    matched = {}
    for i, comment in enumerate(comments):
        for entry in testgen_result.get("results", []):
            if entry.get("comment_text") == comment["text"] and entry.get("success"):
                test_code = entry["test_code"]
                language = entry.get("language", "python")
                ext_map = {
                    "python": ".py",
                    "javascript": ".test.js",
                    "typescript": ".test.ts",
                    "go": "_test.go",
                }
                ext = ext_map.get(language, ".py")
                test_filename = f"test_review_comment_{i}{ext}"
                matched[i] = (comment, test_code, test_filename)
                break
    return matched


def run_groundtruth_assessment(
    *,
    session: "DockerContainerSession",
    instance: dict,
    testgen_result: dict | None,
) -> list[dict]:
    """Run groundtruth tests (from testgen_combined) and return per-comment results.

    Runs inside the already-active Docker container so the agent's changes are
    already present in /workspace.
    """
    if testgen_result is None:
        return []

    comments = instance["reference_review_comments"]

    language = "python"
    for entry in testgen_result.get("results", []):
        if entry.get("success"):
            language = entry.get("language", "python")
            break

    matched = match_tests_to_comments(comments, testgen_result)
    assessment: list[dict] = []
    for comment_index in sorted(matched.keys()):
        comment, test_code, test_filename = matched[comment_index]
        details = verify_with_test_details(session, test_code, test_filename, language)
        assessment.append({
            "comment_index": comment_index,
            "comment_text": comment.get("text", ""),
            "test_filename": test_filename,
            "passed": details["passed"],
            "output": details["output"],
            "returncode": details["returncode"],
            "elapsed_seconds": details.get("elapsed_seconds"),
        })
    return assessment


def load_docker_image_name(docker_image_map_file: Path, instance_id: str) -> str | None:
    """Load the selected Docker image for an instance from the CSV map."""
    if not docker_image_map_file.exists():
        raise FileNotFoundError(
            f"Docker image map file not found: {docker_image_map_file}"
        )

    with docker_image_map_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("instance_id") == instance_id:
                selected_image = (row.get("selected_image") or "").strip()
                return selected_image or None
    return None


def match_validation_tests_to_comments(
    *,
    instance: dict,
    validation_result: dict | None,
    validation_test_dir: Path,
) -> dict[int, dict]:
    """Match successful generated validation tests to canonical review comments."""
    matched: dict[int, dict] = {}
    slug = instance_slug(instance["instance_id"])
    comments = instance.get("reference_review_comments", [])
    validation_entries = (validation_result or {}).get("results", [])

    for comment_index, comment in enumerate(comments):
        for entry in validation_entries:
            if entry.get("comment_text") != comment.get("text") or not entry.get("success"):
                continue

            language = entry.get("language", "python")
            test_file = entry.get("test_file")
            if test_file:
                test_filename = Path(test_file).name
            else:
                test_filename = (
                    f"test_review_comment_{comment_index}"
                    f"{LANGUAGE_EXTENSIONS.get(language, '.py')}"
                )
            source_test_path = validation_test_dir / slug / test_filename
            matched[comment_index] = {
                "comment": comment,
                "language": language,
                "test_filename": test_filename,
                "test_code": entry.get("test_code", ""),
                "source_test_path": source_test_path if source_test_path.exists() else None,
                "source_result": entry,
            }
            break

    return matched


def synthesize_validation_tests_for_comments(instance: dict) -> dict[int, dict]:
    """Create placeholder validation-test specs for Qwen to author in Docker."""
    synthesized: dict[int, dict] = {}
    for comment_index, comment in enumerate(instance.get("reference_review_comments", [])):
        synthesized[comment_index] = {
            "comment": comment,
            "language": "python",
            "test_filename": f"test_review_comment_{comment_index}.py",
            "test_code": "",
            "source_test_path": None,
            "source_result": None,
            "generated_by_agent": True,
        }
    return synthesized


def make_empty_result(
    *,
    instance: dict,
    model: str,
    error: str,
) -> dict:
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "agent": "qwen-code-validation-test",
        "model": model,
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


def process_instance(
    *,
    instance: dict,
    validation_result: dict | None,
    validation_test_dir: Path,
    testgen_results: dict | None,
    output_dir: Path,
    model: str,
    docker_image: str,
    qwen_settings_path: Path,
) -> dict:
    """Resolve one instance using generated validation tests, then assess with groundtruth tests."""
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    instance_dir = output_dir / instance_slug(instance_id)
    instance_dir.mkdir(parents=True, exist_ok=True)

    validation_tests = match_validation_tests_to_comments(
        instance=instance,
        validation_result=validation_result,
        validation_test_dir=validation_test_dir,
    )
    if not validation_tests:
        logger.warning(
            "No generated validation tests found for %s; Qwen will be asked to create them",
            instance_id,
        )
        validation_tests = synthesize_validation_tests_for_comments(instance)

    logger.info(
        "Processing instance: %s (%d validation tests)",
        instance_id,
        len(validation_tests),
    )

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-agent-val-{safe_name}"
    rm_result = subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
        text=True,
    )
    if rm_result.returncode == 0 and rm_result.stdout.strip():
        time.sleep(2)

    qwen_auth_type, qwen_env = get_qwen_auth_config(qwen_settings_path)
    volumes = get_qwen_mounts(qwen_settings_path)
    session = DockerContainerSession(
        docker_image,
        name=container_name,
        env=qwen_env,
        volumes=volumes,
    )

    groundtruth_assessment: list[dict] = []

    try:
        session.start()
        logger.info("Started container %s (image: %s)", container_name, docker_image)
        setup_qwen_in_container(session)

        batch_result = resolve_instance_with_validation_tests(
            instance=instance,
            validation_tests=validation_tests,
            session=session,
            model=model,
            qwen_auth_type=qwen_auth_type,
            artifact_dir=instance_dir,
        )
        resolutions = [resolution.to_dict() for resolution in batch_result.resolutions]

        # Run groundtruth tests (testgen_combined) for assessment while the
        # container is still live and the agent's changes are in /workspace.
        if testgen_results is not None:
            logger.info("Running groundtruth assessment tests for %s", instance_id)
            groundtruth_assessment = run_groundtruth_assessment(
                session=session,
                instance=instance,
                testgen_result=testgen_results,
            )
            gt_pass = sum(1 for r in groundtruth_assessment if r["passed"])
            logger.info(
                "  Groundtruth assessment: %d/%d passed",
                gt_pass,
                len(groundtruth_assessment),
            )
        else:
            logger.warning(
                "No groundtruth testgen results for %s; skipping assessment", instance_id
            )

    finally:
        session.remove(force=True)
        logger.info("Removed container %s", container_name)

    num_comments = len(resolutions)
    num_gt = len(groundtruth_assessment)
    num_gt_passed = sum(1 for r in groundtruth_assessment if r["passed"])
    # Resolution is defined by groundtruth tests, not validation tests.
    num_resolved = num_gt_passed
    resolution_rate = num_gt_passed / num_gt if num_gt else 0.0

    result = {
        "instance_id": instance_id,
        "repo": repo,
        "agent": "qwen-code-validation-test",
        "model": model,
        "num_comments": num_comments,
        "num_resolved": num_resolved,
        "resolution_rate": resolution_rate,
        "num_expected_failures_observed": sum(
            1 for row in resolutions if row["expected_failure_observed"]
        ),
        "num_initial_unexpected_passes": sum(
            1 for row in resolutions if row["initial_unexpected_pass"]
        ),
        "num_validation_tests_revised": sum(
            1 for row in resolutions if row["validation_test_revised"]
        ),
        "results": resolutions,
        "groundtruth_assessment": {
            "num_tests": num_gt,
            "num_passed": num_gt_passed,
            "pass_rate": num_gt_passed / num_gt if num_gt else None,
            "results": groundtruth_assessment,
        },
        "trajectory": {
            "format": "agent_stdout",
            "path": batch_result.artifacts.get("trajectory.json"),
        },
        "artifacts": batch_result.artifacts,
    }

    result_file = instance_dir / "result.json"
    result_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    logger.info(
        "Result saved to %s (groundtruth: %d/%d passed = %.1f%%)",
        result_file,
        num_gt_passed,
        num_gt,
        resolution_rate * 100,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve review comments using generated validation tests"
    )
    parser.add_argument("--instance-id", type=str, required=True)
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
        help="Qwen model to use (default: use configured Qwen default)",
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

    dataset_file = Path(args.dataset_file)
    validation_test_dir = Path(args.validation_test_dir)
    testgen_dir = Path(args.testgen_dir)
    output_dir = Path(args.output_dir)
    docker_image_map_file = Path(args.docker_image_map)
    qwen_settings_path = Path(args.qwen_settings)
    output_dir.mkdir(parents=True, exist_ok=True)

    instance = load_dataset_instance(dataset_file, args.instance_id)
    if instance is None:
        logger.error("Instance %s not found in %s", args.instance_id, dataset_file)
        sys.exit(1)

    validation_result = load_validation_result(validation_test_dir, args.instance_id)
    if validation_result is None:
        logger.warning(
            "Validation-test results not found for %s in %s; Qwen will be asked to create tests",
            args.instance_id,
            validation_test_dir,
        )

    testgen_results = load_testgen_results(testgen_dir, args.instance_id)
    if testgen_results is None:
        logger.error(
            "Testgen results not found for %s in %s",
            args.instance_id,
            testgen_dir,
        )
        sys.exit(1)

    try:
        docker_image = load_docker_image_name(docker_image_map_file, args.instance_id)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)
    if not docker_image:
        logger.error(
            "Docker image not found for %s in %s",
            args.instance_id,
            docker_image_map_file,
        )
        sys.exit(1)

    if not qwen_settings_path.exists():
        logger.warning(
            "Qwen settings file not found: %s (container may fail to authenticate)",
            qwen_settings_path,
        )

    started = time.time()
    result = process_instance(
        instance=instance,
        validation_result=validation_result,
        validation_test_dir=validation_test_dir,
        testgen_results=testgen_results,
        output_dir=output_dir,
        model=args.model,
        docker_image=docker_image,
        qwen_settings_path=qwen_settings_path,
    )
    elapsed = time.time() - started
    logger.info(
        "=== DONE === %s: %d/%d resolved (%.1f%%) in %.1fs",
        args.instance_id,
        result["num_resolved"],
        result["num_comments"],
        result["resolution_rate"] * 100,
        elapsed,
    )


if __name__ == "__main__":
    main()
