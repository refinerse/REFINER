#!/usr/bin/env python3
"""Per-instance intent-guided agent resolution with Qwen Code."""

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
)
from pipeline.agent_resolver_with_task import (
    AGENT_NAME,
    DEFAULT_INTENT_FILE,
    load_precomputed_intents,
    resolve_instance_with_intent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = ""
DEFAULT_TESTGEN_DIR = "testgen_combined"
DEFAULT_dataset_FILE = "dataset/instances.jsonl"
DEFAULT_OUTPUT_DIR = "results_agent_resolution_with_intent"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"
DEFAULT_QWEN_SETTINGS = Path.home() / ".qwen" / "settings.json"


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


def load_testgen_results(testgen_dir: Path, instance_id: str) -> dict | None:
    """Load testgen result.json for an instance."""
    slug = instance_id.replace("/", "__")
    result_file = testgen_dir / slug / "result.json"
    if not result_file.exists():
        return None
    return json.loads(result_file.read_text(encoding="utf-8"))


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
                if selected_image:
                    return selected_image
                return None
    return None


def match_tests_to_comments(
    comments: list[dict], testgen_result: dict
) -> dict[int, tuple[dict, str, str]]:
    """Match Stage 3 comments to their verified test code."""
    matched = {}
    for index, comment in enumerate(comments):
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
                test_filename = f"test_review_comment_{index}{ext}"
                matched[index] = (comment, test_code, test_filename)
                break
    return matched


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


def process_instance(
    instance: dict,
    testgen_results: dict,
    output_dir: Path,
    model: str,
    docker_image: str,
    qwen_settings_path: Path,
    intent_file_path: Path,
) -> dict:
    """Process a single instance with intent guidance."""
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    comments = instance["reference_review_comments"]

    logger.info("Processing instance with intent: %s (%d comments)", instance_id, len(comments))

    instance_dir = output_dir / instance_id.replace("/", "__")
    instance_dir.mkdir(parents=True, exist_ok=True)

    intent_lookup = load_precomputed_intents(intent_file_path)

    matched = match_tests_to_comments(comments, testgen_results)
    if not matched:
        logger.warning("No verified tests found for %s", instance_id)
        result = {
            "instance_id": instance_id,
            "repo": repo,
            "agent": AGENT_NAME,
            "model": model,
            "intent_file": str(intent_file_path),
            "intent_by_comment_index": {},
            "num_comments": 0,
            "num_resolved": 0,
            "resolution_rate": 0.0,
            "results": [],
            "error": "No verified Stage 3 tests to match",
        }
        result_file = instance_dir / "result.json"
        result_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        return result

    logger.info("  Matched %d comment(s) with Stage 3 tests", len(matched))

    language = "python"
    for entry in testgen_results.get("results", []):
        if entry.get("success"):
            language = entry.get("language", "python")
            break

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-agent-intent-{safe_name}"

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

    resolutions: list[dict] = []
    artifacts: dict[str, str] = {}

    try:
        session.start()
        logger.info("Started container %s (image: %s)", container_name, docker_image)

        setup_qwen_in_container(session)

        for index in sorted(matched.keys()):
            comment = matched[index][0]
            intent = intent_lookup.get((instance_id, index), "other")
            logger.info(
                "  Comment %d [%s]: [%s] %s",
                index,
                intent,
                comment["path"],
                comment["text"][:80],
            )

        batch_result = resolve_instance_with_intent(
            instance=instance,
            matched_comments=matched,
            session=session,
            model=model,
            language=language,
            qwen_auth_type=qwen_auth_type,
            artifact_dir=instance_dir,
            intent_lookup=intent_lookup,
        )
        results = batch_result.resolutions
        artifacts = batch_result.artifacts

        for resolution in results:
            row = resolution.to_dict()
            row["edit_intent"] = intent_lookup.get(
                (instance_id, resolution.comment_index),
                "other",
            )
            resolutions.append(row)
            logger.info(
                "  Comment %d: %s (test=%s, intent=%s, error=%s)",
                resolution.comment_index,
                "RESOLVED" if resolution.resolved else "NOT RESOLVED",
                "PASS" if resolution.test_passed else "FAIL",
                row["edit_intent"],
                resolution.error or "none",
            )

    finally:
        session.remove(force=True)
        logger.info("Removed container %s", container_name)

    num_comments = len(resolutions)
    num_resolved = sum(1 for resolution in resolutions if resolution["resolved"])
    resolution_rate = num_resolved / num_comments if num_comments > 0 else 0.0
    intent_by_comment_index = _intent_metadata_for_results(
        instance_id=instance_id,
        comment_indices=sorted(matched.keys()),
        intent_lookup=intent_lookup,
    )

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
        "results": resolutions,
        "trajectory": {
            "format": "agent_stdout",
            "path": artifacts.get("trajectory.json"),
        },
        "artifacts": artifacts,
    }

    result_file = instance_dir / "result.json"
    result_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    logger.info(
        "Result saved to %s (resolved: %d/%d = %.1f%%)",
        result_file,
        num_resolved,
        num_comments,
        resolution_rate * 100,
    )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve review comments with Qwen Code and intent guidance"
    )
    parser.add_argument(
        "--instance-id",
        type=str,
        required=True,
        help="Instance ID to process",
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
        help="Qwen model to use (default: use the configured Qwen default)",
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
            "Intent file not found: %s (all comments use naive fallback)",
            intent_file_path,
        )

    started = time.time()
    result = process_instance(
        instance=instance,
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
