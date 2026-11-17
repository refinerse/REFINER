#!/usr/bin/env python3
"""Per-instance validation-test and intent guided agent resolution."""

from __future__ import annotations

import argparse
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
)
from pipeline.agent_resolver_vt_sk import AGENT_NAME, resolve_instance_vt_sk
from pipeline.agent_resolver_with_task import (
    DEFAULT_INTENT_FILE,
    load_precomputed_intents,
)
from run_agent_resolution_validation_test import (
    DEFAULT_DATASET_FILE,
    DEFAULT_DOCKER_IMAGE_MAP_FILE,
    DEFAULT_MODEL,
    DEFAULT_QWEN_SETTINGS,
    DEFAULT_TESTGEN_DIR,
    DEFAULT_VALIDATION_TEST_DIR,
    instance_slug,
    load_dataset_instance,
    load_docker_image_name,
    load_testgen_results,
    load_validation_result,
    match_validation_tests_to_comments,
    run_groundtruth_assessment,
    synthesize_validation_tests_for_comments,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "results_agent_resolution_vt_sk"


def _intent_metadata_for_results(
    *,
    instance_id: str,
    comment_indices: list[int],
    intent_lookup: dict[tuple[str, int], str],
) -> dict[str, str]:
    return {
        str(index): intent_lookup.get((instance_id, index), "other")
        for index in comment_indices
    }


def make_empty_result(
    *,
    instance: dict,
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
    intent_file_path: Path,
) -> dict:
    """Resolve one instance with validation tests and intent guidance."""
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    instance_dir = output_dir / instance_slug(instance_id)
    instance_dir.mkdir(parents=True, exist_ok=True)

    intent_lookup = load_precomputed_intents(intent_file_path)

    validation_tests = match_validation_tests_to_comments(
        instance=instance,
        validation_result=validation_result,
        validation_test_dir=validation_test_dir,
    )
    # Fallback: any review comment without a matched validation test is still
    # resolved naively from the edit intent (like the with_intent resolver),
    # rather than being dropped. These are marked no_validation_test=True so the
    # resolver skips the copy/run/diff steps and judges them via groundtruth.
    instance_language = instance.get("language", "python")
    n_fallback = 0
    for comment_index, comment in enumerate(instance.get("reference_review_comments", [])):
        if comment_index in validation_tests:
            continue
        validation_tests[comment_index] = {
            "comment": comment,
            "language": instance_language,
            "test_filename": None,
            "test_code": "",
            "source_test_path": None,
            "source_result": None,
            "generated_by_agent": False,
            "no_validation_test": True,
        }
        n_fallback += 1

    logger.info(
        "Processing instance with validation tests and intent: %s "
        "(%d comments: %d with tests, %d naive-intent fallback)",
        instance_id,
        len(validation_tests),
        len(validation_tests) - n_fallback,
        n_fallback,
    )

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-agent-vt-sk-{safe_name}"
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
    batch_result = None
    resolutions: list[dict] = []

    try:
        session.start()
        logger.info("Started container %s (image: %s)", container_name, docker_image)
        setup_qwen_in_container(session)

        batch_result = resolve_instance_vt_sk(
            instance=instance,
            validation_tests=validation_tests,
            session=session,
            model=model,
            qwen_auth_type=qwen_auth_type,
            artifact_dir=instance_dir,
            intent_lookup=intent_lookup,
        )
        for resolution in batch_result.resolutions:
            row = resolution.to_dict()
            row["edit_intent"] = intent_lookup.get(
                (instance_id, resolution.comment_index),
                "other",
            )
            resolutions.append(row)

        if testgen_results is not None:
            logger.info("Running groundtruth assessment tests for %s", instance_id)
            groundtruth_assessment = run_groundtruth_assessment(
                session=session,
                instance=instance,
                testgen_result=testgen_results,
            )
            gt_pass = sum(1 for row in groundtruth_assessment if row["passed"])
            logger.info(
                "  Groundtruth assessment: %d/%d passed",
                gt_pass,
                len(groundtruth_assessment),
            )
        else:
            logger.warning(
                "No groundtruth testgen results for %s; skipping assessment",
                instance_id,
            )

    finally:
        session.remove(force=True)
        logger.info("Removed container %s", container_name)

    num_comments = len(resolutions)
    num_gt = len(groundtruth_assessment)
    num_gt_passed = sum(1 for row in groundtruth_assessment if row["passed"])
    num_resolved = num_gt_passed
    resolution_rate = num_gt_passed / num_gt if num_gt else 0.0
    intent_by_comment_index = _intent_metadata_for_results(
        instance_id=instance_id,
        comment_indices=sorted(validation_tests.keys()),
        intent_lookup=intent_lookup,
    )
    artifacts = batch_result.artifacts if batch_result is not None else {}

    result = {
        "instance_id": instance_id,
        "repo": repo,
        "agent": AGENT_NAME,
        "model": model,
        "intent_file": str(intent_file_path),
        "intent_by_comment_index": intent_by_comment_index,
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
            "path": artifacts.get("trajectory.json"),
        },
        "artifacts": artifacts,
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
        description="Resolve review comments using validation tests and intent guidance"
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
        "--intent-file",
        type=str,
        default=DEFAULT_INTENT_FILE,
        help=f"Comment intent JSONL file (default: {DEFAULT_INTENT_FILE})",
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
    intent_file_path = Path(args.intent_file)
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
    if not intent_file_path.exists():
        logger.warning(
            "Intent file not found: %s (all comments use naive-intent fallback)",
            intent_file_path,
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
        intent_file_path=intent_file_path,
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
