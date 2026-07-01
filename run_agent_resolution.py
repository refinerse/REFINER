#!/usr/bin/env python3
"""Per-instance agent resolution of code review comments with Qwen Code.

Uses Qwen Code inside a Docker container to resolve review comments,
then verifies the agent's changes against Stage 3 tests.

All matched comments for an instance are batched into a single Qwen Code
invocation so the agent sees the full review context and makes one coherent
set of changes.

Usage:
  python run_agent_resolution.py --instance-id <id>
  python run_agent_resolution.py --instance-id <id> --model <qwen-model>
"""

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
    resolve_instance,
    setup_qwen_in_container,
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
DEFAULT_OUTPUT_DIR = "results_agent_resolution"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"
DEFAULT_QWEN_SETTINGS = Path.home() / ".qwen" / "settings.json"


def load_dataset_instance(dataset_file: Path, instance_id: str) -> dict | None:
    """Load a single instance from the dataset JSONL file."""
    with dataset_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            inst = json.loads(line)
            if inst["instance_id"] == instance_id:
                return inst
    return None


def load_testgen_results(testgen_dir: Path, instance_id: str) -> dict | None:
    """Load testgen result.json for an instance."""
    slug = instance_id.replace("/", "__")
    result_file = testgen_dir / slug / "result.json"
    if not result_file.exists():
        return None
    return json.loads(result_file.read_text())


def load_docker_image_name(docker_image_map_file: Path, instance_id: str) -> str | None:
    """Load the selected Docker image for an instance from the CSV map."""
    if not docker_image_map_file.exists():
        raise FileNotFoundError(
            f"Docker image map file not found: {docker_image_map_file}"
        )

    with docker_image_map_file.open(newline="") as f:
        reader = csv.DictReader(f)
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


def process_instance(
    instance: dict,
    testgen_results: dict,
    output_dir: Path,
    model: str,
    docker_image: str,
    qwen_settings_path: Path,
) -> dict:
    """Process a single instance: resolve all comments together and verify.

    Flow:
    1. Start Docker container with Qwen settings mounted read-only
    2. Setup: create agent user, install Qwen Code, chown workspace
    3. Match comments to Stage 3 tests
    4. Build a single prompt with all comments, invoke Qwen Code once
    5. Verify each Stage 3 test individually
    6. Save result.json
    7. Remove container
    """
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    comments = instance["reference_review_comments"]

    logger.info("Processing instance: %s (%d comments)", instance_id, len(comments))

    instance_dir = output_dir / instance_id.replace("/", "__")
    instance_dir.mkdir(parents=True, exist_ok=True)

    # Match comments to Stage 3 tests
    matched = match_tests_to_comments(comments, testgen_results)
    if not matched:
        logger.warning("No verified tests found for %s", instance_id)
        result = {
            "instance_id": instance_id,
            "repo": repo,
            "agent": "qwen-code",
            "model": model,
            "num_comments": 0,
            "num_resolved": 0,
            "resolution_rate": 0.0,
            "results": [],
            "error": "No verified Stage 3 tests to match",
        }
        result_file = instance_dir / "result.json"
        result_file.write_text(json.dumps(result, indent=2, default=str))
        return result

    logger.info("  Matched %d comment(s) with Stage 3 tests", len(matched))

    # Determine language from first matched test
    language = "python"
    for entry in testgen_results.get("results", []):
        if entry.get("success"):
            language = entry.get("language", "python")
            break

    # Start container
    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-agent-{safe_name}"

    # Remove any stale container
    rm_result = subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True, text=True,
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

        # Setup Qwen Code in container
        setup_qwen_in_container(session)

        # Log comments being resolved
        for i in sorted(matched.keys()):
            comment = matched[i][0]
            logger.info("  Comment %d: [%s] %s", i, comment["path"], comment["text"][:80])

        # Resolve all comments in a single Qwen invocation
        batch_result = resolve_instance(
            instance=instance,
            matched_comments=matched,
            session=session,
            model=model,
            language=language,
            qwen_auth_type=qwen_auth_type,
            artifact_dir=instance_dir,
        )
        results = batch_result.resolutions
        artifacts = batch_result.artifacts

        for r in results:
            resolutions.append(r.to_dict())
            logger.info(
                "  Comment %d: %s (test=%s, error=%s)",
                r.comment_index,
                "RESOLVED" if r.resolved else "NOT RESOLVED",
                "PASS" if r.test_passed else "FAIL",
                r.error or "none",
            )

    finally:
        session.remove(force=True)
        logger.info("Removed container %s", container_name)

    # Compute stats
    num_comments = len(resolutions)
    num_resolved = sum(1 for r in resolutions if r["resolved"])
    resolution_rate = num_resolved / num_comments if num_comments > 0 else 0.0

    result = {
        "instance_id": instance_id,
        "repo": repo,
        "agent": "qwen-code",
        "model": model,
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

    # Save result
    result_file = instance_dir / "result.json"
    result_file.write_text(json.dumps(result, indent=2, default=str))
    logger.info(
        "Result saved to %s (resolved: %d/%d = %.1f%%)",
        result_file, num_resolved, num_comments, resolution_rate * 100,
    )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Resolve review comments using Qwen Code in Docker"
    )
    parser.add_argument(
        "--instance-id", type=str, required=True,
        help="Instance ID to process",
    )
    parser.add_argument(
        "--dataset-file", type=str, default=DEFAULT_dataset_FILE,
        help=f"Stage 3 JSONL file (default: {DEFAULT_dataset_FILE})",
    )
    parser.add_argument(
        "--testgen-dir", type=str, default=DEFAULT_TESTGEN_DIR,
        help=f"Testgen results directory (default: {DEFAULT_TESTGEN_DIR})",
    )
    parser.add_argument(
        "--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--docker-image-map", type=str, default=DEFAULT_DOCKER_IMAGE_MAP_FILE,
        help=(
            "CSV mapping file with selected Docker images "
            f"(default: {DEFAULT_DOCKER_IMAGE_MAP_FILE})"
        ),
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help="Qwen model to use (default: use the default configured in Qwen settings)",
    )
    parser.add_argument(
        "--qwen-settings", "--credentials", dest="qwen_settings", type=str,
        default=str(DEFAULT_QWEN_SETTINGS),
        help=f"Path to Qwen settings.json (default: {DEFAULT_QWEN_SETTINGS})",
    )

    args = parser.parse_args()

    dataset_file = Path(args.dataset_file)
    testgen_dir = Path(args.testgen_dir)
    output_dir = Path(args.output_dir)
    docker_image_map_file = Path(args.docker_image_map)
    qwen_settings_path = Path(args.qwen_settings)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load instance from dataset
    instance = load_dataset_instance(dataset_file, args.instance_id)
    if instance is None:
        logger.error("Instance %s not found in %s", args.instance_id, dataset_file)
        sys.exit(1)

    # Load testgen results
    testgen_results = load_testgen_results(testgen_dir, args.instance_id)
    if testgen_results is None:
        logger.error(
            "Testgen results not found for %s in %s",
            args.instance_id, testgen_dir,
        )
        sys.exit(1)

    # Get Docker image
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

    # Check Qwen settings
    if not qwen_settings_path.exists():
        logger.warning(
            "Qwen settings file not found: %s (container may fail to authenticate)",
            qwen_settings_path,
        )

    t0 = time.time()
    result = process_instance(
        instance=instance,
        testgen_results=testgen_results,
        output_dir=output_dir,
        model=args.model,
        docker_image=docker_image,
        qwen_settings_path=qwen_settings_path,
    )
    elapsed = time.time() - t0

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
