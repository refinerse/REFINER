#!/usr/bin/env python3
"""Replay stored agent patches in Docker and run verified acceptance tests.

For each instance in the dataset, this script:
1. Locates the stored patch in agent_resolution_combined/<instance_id>/result.json
2. Locates successful generated tests in testgen_combined/<instance_id>/result.json
3. Starts the corresponding reviewbench Docker image
4. Resets the repo to commit_to_review.head_commit
5. Applies the stored unified diff with git apply
6. Runs each verified acceptance test in isolation
7. Writes per-instance results and an aggregate summary

Usage:
  python run_batch_patch_verification.py --limit 5 --workers 2
  python run_batch_patch_verification.py --repo tobymao/sqlglot
  python run_batch_patch_verification.py --no-resume
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

from execution.container_runtime import (
    DockerContainerSession,
    docker_image_exists,
    get_docker_image_name,
)
from pipeline.agent_resolver import verify_with_test

# Parse pytest summary tokens like "3 passed", "1 failed", "2 errors".
_PYTEST_SUMMARY_RE = re.compile(
    r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed)"
)


def parse_pytest_counts(output: str) -> dict[str, int]:
    """Extract passed/failed/error counts from the last pytest summary line."""
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    for line in reversed(output.splitlines()):
        matches = _PYTEST_SUMMARY_RE.findall(line)
        if not matches:
            continue
        for num, kind in matches:
            key = "error" if kind in ("error", "errors") else kind
            if key in counts:
                counts[key] += int(num)
        break
    return counts


def verify_with_counts(
    session: DockerContainerSession,
    test_code: str,
    test_filename: str,
    language: str,
) -> dict:
    """Run one acceptance test and return pass/fail plus per-assertion counts.

    Python tests (already split into one function per assertion) run under
    pytest *without* ``-x`` so every sub-test executes and we can report how
    many assertions pass. Non-python tests run via the standard single
    pass/fail path and count as one assertion.
    """
    if language != "python":
        passed, output = verify_with_test(
            session=session,
            test_code=test_code,
            test_filename=test_filename,
            language=language,
        )
        return {
            "passed": passed,
            "output": output,
            "num_assertions": 1,
            "assertions_passed": 1 if passed else 0,
            "assertions_failed": 0 if passed else 1,
        }

    import tempfile

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
        f"python -m pytest {container_test_path} -v --tb=short --no-header "
        f"-c /dev/null -p no:cacheprovider"
    )
    result = session.run_command(run_cmd, timeout=120)
    combined = (result.stdout + "\n" + result.stderr).strip()
    counts = parse_pytest_counts(combined)
    total = counts["passed"] + counts["failed"] + counts["error"]
    return {
        "passed": result.returncode == 0,
        "output": combined,
        "num_assertions": total,
        "assertions_passed": counts["passed"],
        "assertions_failed": counts["failed"] + counts["error"],
    }

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_DATASET_FILE = "dataset/instances.jsonl"
DEFAULT_PATCH_DIR = "agent_resolution_combined"
DEFAULT_TESTGEN_DIR = "testgen_combined"
DEFAULT_OUTPUT_DIR = "results_patch_replay"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"

LANGUAGE_EXTENSIONS = {
    "python": ".py",
    "javascript": ".test.js",
    "typescript": ".test.ts",
    "go": "_test.go",
}

BINARY_DIFF_MARKERS = (
    "GIT binary patch",
    "Binary files ",
)


def get_fallback_docker_image_name(instance_id: str) -> str:
    """Derive the GHCR fallback image name from an instance ID."""
    slug = instance_id.split("@")[0].lower()
    return f"ghcr.io/c-crab-benchmark/{slug}"


def resolve_docker_image(instance_id: str) -> str:
    """Resolve the image to use, falling back from reviewbench to GHCR."""
    primary_image = get_docker_image_name(instance_id)
    if docker_image_exists(primary_image):
        return primary_image

    fallback_image = get_fallback_docker_image_name(instance_id)
    if docker_image_exists(fallback_image):
        return fallback_image

    # Let docker attempt a registry pull for the fallback image at runtime.
    return fallback_image


def load_docker_image_map(docker_image_map_file: Path) -> dict[str, str]:
    """Load precomputed, locally-available images from the instance/image CSV.

    Using the CSV's ``selected_image`` avoids live Docker probing that could
    otherwise fall through to a registry pull (same approach as
    ``run_batch_gt_validation.py``).
    """
    mapping: dict[str, str] = {}
    if not docker_image_map_file.exists():
        logger.warning("Docker image map file not found: %s", docker_image_map_file)
        return mapping
    with docker_image_map_file.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            instance_id = (row.get("instance_id") or "").strip()
            selected_image = (row.get("selected_image") or "").strip()
            if instance_id and selected_image:
                mapping[instance_id] = selected_image
    return mapping


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


def load_combined_result(base_dir: Path, instance_id: str) -> dict | None:
    """Load result.json from a combined output directory keyed by instance_id."""
    result_file = base_dir / instance_id / "result.json"
    if not result_file.exists():
        return None
    return json.loads(result_file.read_text(encoding="utf-8"))


def load_existing_result(output_dir: Path, instance_id: str) -> dict | None:
    """Load an existing output result.json for an instance, or None."""
    result_file = output_dir / instance_id / "result.json"
    if not result_file.exists():
        return None
    try:
        return json.loads(result_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load existing result for %s: %s", instance_id, exc)
        return None


def verified_tests_from_result(instance: dict, testgen_result: dict) -> list[dict]:
    """Extract successful generated tests matched to the instance comment order.

    We cannot trust ``comment_index`` in the stored testgen result because replay
    needs to map tests back to the dataset's canonical review comments. Match by
    exact ``comment_text`` against ``reference_review_comments`` and then rebuild
    the normalized test filename from the dataset comment index.
    """
    verified = []
    comments = instance.get("reference_review_comments", [])

    for comment_index, comment in enumerate(comments):
        for entry in testgen_result.get("results", []):
            if entry.get("comment_text") != comment.get("text") or not entry.get("success"):
                continue

            language = entry.get("language", "python")
            ext = LANGUAGE_EXTENSIONS.get(language, ".py")
            verified.append(
                {
                    "comment_index": comment_index,
                    "comment_text": comment.get("text", ""),
                    "comment_type": entry.get("comment_type") or comment.get("type"),
                    "language": language,
                    "test_file": f"test_review_comment_{comment_index}{ext}",
                    "test_code": entry.get("test_code", ""),
                }
            )
            break

    return verified


def select_agent_diff(patch_result: dict) -> tuple[str | None, str | None]:
    """Pick the stored diff to replay, ensuring it is non-empty and consistent."""
    diffs = []
    for entry in patch_result.get("results", []):
        diff = entry.get("agent_diff", "")
        if diff and diff.strip():
            diffs.append(diff)

    if not diffs:
        return None, "No non-empty agent_diff found"

    unique_diffs = list(dict.fromkeys(diffs))
    if len(unique_diffs) > 1:
        return None, f"Found {len(unique_diffs)} conflicting non-empty agent diffs"

    return unique_diffs[0], None


def make_stub_result(
    instance: dict,
    *,
    error: str,
    patch_applied: bool = False,
    patch_apply_output: str = "",
    patch_diff: str = "",
    results: list[dict] | None = None,
) -> dict:
    """Create a standard failure/skip result payload."""
    test_results = results or []
    num_tests = len(test_results)
    num_passed = sum(1 for entry in test_results if entry.get("test_passed"))
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "patch_applied": patch_applied,
        "patch_apply_output": patch_apply_output,
        "patch_diff": patch_diff,
        "num_tests": num_tests,
        "num_tests_passed": num_passed,
        "test_pass_rate": (num_passed / num_tests) if num_tests else 0.0,
        "results": test_results,
        "error": error,
    }


def placeholder_results_for_tests(
    verified_tests: list[dict],
    *,
    error: str | None = None,
    test_output: str = "",
) -> list[dict]:
    """Build placeholder result rows for matched tests that were not executed."""
    return [
        {
            "comment_index": test["comment_index"],
            "comment_text": test["comment_text"],
            "comment_type": test["comment_type"],
            "language": test["language"],
            "test_file": test["test_file"],
            "test_passed": False,
            "test_output": test_output,
            "error": error,
        }
        for test in verified_tests
    ]


def write_instance_result(output_dir: Path, result: dict) -> None:
    """Persist a per-instance result.json."""
    instance_dir = output_dir / result["instance_id"]
    instance_dir.mkdir(parents=True, exist_ok=True)
    result_file = instance_dir / "result.json"
    result_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")


def ensure_git_safe_directory(session: DockerContainerSession) -> None:
    """Allow git commands in /workspace inside the container."""
    result = session.run_command(
        "git config --global --add safe.directory /workspace",
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to configure git safe.directory: "
            f"{(result.stderr or result.stdout)[-1000:]}"
        )


def reinstall_python_repo(session: DockerContainerSession) -> None:
    """Install the workspace package in editable mode."""
    session.run_command("pip install -e . --no-deps --quiet", timeout=120)


def apply_patch_in_container(
    session: DockerContainerSession,
    patch_diff: str,
) -> tuple[bool, str]:
    """Copy a unified diff into the container and apply it with git apply."""
    patch_diff, stripped_binary_paths = strip_binary_file_patches(patch_diff)
    if not patch_diff.strip():
        note = ""
        if stripped_binary_paths:
            note = (
                "Ignored binary-only patch sections for: "
                + ", ".join(stripped_binary_paths)
            )
        return True, note

    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as handle:
        handle.write(patch_diff)
        local_patch = Path(handle.name)

    container_patch = "/tmp/replay.patch"
    try:
        session.copy_to(local_patch, container_patch)
    finally:
        local_patch.unlink(missing_ok=True)

    check_result = session.run_command(
        f"git apply --check {container_patch}",
        timeout=60,
    )
    combined_output = (check_result.stdout + "\n" + check_result.stderr).strip()
    if stripped_binary_paths:
        binary_note = (
            "Ignored binary patch sections for: "
            + ", ".join(stripped_binary_paths)
        )
        combined_output = "\n".join(
            part for part in [binary_note, combined_output] if part
        ).strip()
    if check_result.returncode != 0:
        return False, combined_output

    apply_result = session.run_command(
        f"git apply {container_patch}",
        timeout=60,
    )
    apply_output = (apply_result.stdout + "\n" + apply_result.stderr).strip()
    combined_output = "\n".join(part for part in [combined_output, apply_output] if part).strip()
    if apply_result.returncode != 0:
        return False, combined_output

    session.run_command(f"rm -f {container_patch}", timeout=10)
    return True, combined_output


def strip_binary_file_patches(patch_diff: str) -> tuple[str, list[str]]:
    """Remove binary-file diff sections so git apply can replay text hunks.

    Some stored diffs contain entries like `.xlsx` fixtures represented as
    `Binary files ... differ` or `GIT binary patch`. Those sections are not
    replayable with our plain `git apply` flow, but the surrounding text hunks
    are still useful for verification.
    """
    if not patch_diff.strip():
        return patch_diff, []

    lines = patch_diff.splitlines(keepends=True)
    sections: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("diff --git "):
            if current:
                sections.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append(current)

    kept_sections: list[str] = []
    stripped_paths: list[str] = []

    for section in sections:
        section_text = "".join(section)
        if any(marker in section_text for marker in BINARY_DIFF_MARKERS):
            header = section[0].strip() if section else ""
            parts = header.split()
            if len(parts) >= 4:
                stripped_paths.append(parts[3].removeprefix("b/"))
            else:
                stripped_paths.append("<unknown>")
            continue
        kept_sections.append(section_text)

    return "".join(kept_sections), stripped_paths


def process_instance(
    instance: dict,
    patch_result: dict,
    testgen_result: dict,
    output_dir: Path,
    docker_image: str,
) -> dict:
    """Replay the stored patch for one instance and verify successful tests."""
    instance_id = instance["instance_id"]
    verified_tests = verified_tests_from_result(instance, testgen_result)
    if not verified_tests:
        result = make_stub_result(instance, error="No successful generated tests found")
        write_instance_result(output_dir, result)
        return result

    patch_diff, patch_error = select_agent_diff(patch_result)
    if patch_error or patch_diff is None:
        error_message = patch_error or "No replayable patch diff found"
        result = make_stub_result(
            instance,
            error=error_message,
            results=placeholder_results_for_tests(
                verified_tests,
                error=error_message,
            ),
        )
        write_instance_result(output_dir, result)
        return result

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-patchreplay-{safe_name}"

    rm_result = subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
        text=True,
    )
    if rm_result.returncode == 0 and rm_result.stdout.strip():
        time.sleep(2)

    session = DockerContainerSession(docker_image, name=container_name)
    test_results: list[dict] = []
    patch_apply_output = ""
    patch_applied = False

    try:
        session.start()
        ensure_git_safe_directory(session)

        head_commit = instance["commit_to_review"]["head_commit"]
        reset_result = session.run_command(
            f"git checkout --force {head_commit} && git clean -fd --quiet",
            timeout=120,
        )
        if reset_result.returncode != 0:
            error_message = f"git checkout failed: {reset_result.stderr[:500]}"
            result = make_stub_result(
                instance,
                error=error_message,
                patch_diff=patch_diff,
                results=placeholder_results_for_tests(
                    verified_tests,
                    error=error_message,
                ),
            )
            write_instance_result(output_dir, result)
            return result

        if any(test["language"] == "python" for test in verified_tests):
            reinstall_python_repo(session)

        patch_applied, patch_apply_output = apply_patch_in_container(session, patch_diff)
        if not patch_applied:
            error_message = "git apply failed"
            result = make_stub_result(
                instance,
                error=error_message,
                patch_applied=False,
                patch_apply_output=patch_apply_output,
                patch_diff=patch_diff,
                results=placeholder_results_for_tests(
                    verified_tests,
                    error=error_message,
                    test_output=patch_apply_output,
                ),
            )
            write_instance_result(output_dir, result)
            return result

        if any(test["language"] == "python" for test in verified_tests):
            reinstall_python_repo(session)

        diff_result = session.run_command("git diff", timeout=30)
        applied_diff = diff_result.stdout
        if not applied_diff.strip():
            status_result = session.run_command("git status --porcelain", timeout=15)
            if not status_result.stdout.strip():
                error_message = "Patch applied but produced no working tree changes"
                result = make_stub_result(
                    instance,
                    error=error_message,
                    patch_applied=True,
                    patch_apply_output=patch_apply_output,
                    patch_diff=patch_diff,
                    results=placeholder_results_for_tests(
                        verified_tests,
                        error=error_message,
                    ),
                )
                write_instance_result(output_dir, result)
                return result
        else:
            patch_diff = applied_diff

        for test in verified_tests:
            info = verify_with_counts(
                session=session,
                test_code=test["test_code"],
                test_filename=test["test_file"],
                language=test["language"],
            )
            test_results.append(
                {
                    "comment_index": test["comment_index"],
                    "comment_text": test["comment_text"],
                    "comment_type": test["comment_type"],
                    "language": test["language"],
                    "test_file": test["test_file"],
                    "test_passed": info["passed"],
                    "num_assertions": info["num_assertions"],
                    "assertions_passed": info["assertions_passed"],
                    "assertions_failed": info["assertions_failed"],
                    "test_output": info["output"],
                    "error": None,
                }
            )

    except Exception as exc:
        logger.exception("[%s] Error replaying patch", instance_id)
        error_message = str(exc)
        result = make_stub_result(
            instance,
            error=error_message,
            patch_applied=patch_applied,
            patch_apply_output=patch_apply_output,
            patch_diff=patch_diff,
            results=test_results or placeholder_results_for_tests(
                verified_tests,
                error=error_message,
            ),
        )
        write_instance_result(output_dir, result)
        return result
    finally:
        session.remove(force=True)

    num_tests = len(test_results)
    num_passed = sum(1 for entry in test_results if entry["test_passed"])
    total_assertions = sum(entry.get("num_assertions", 0) for entry in test_results)
    assertions_passed = sum(entry.get("assertions_passed", 0) for entry in test_results)
    result = {
        "instance_id": instance_id,
        "repo": instance["repo"],
        "patch_applied": True,
        "patch_apply_output": patch_apply_output,
        "patch_diff": patch_diff,
        "num_tests": num_tests,
        "num_tests_passed": num_passed,
        "test_pass_rate": (num_passed / num_tests) if num_tests else 0.0,
        "total_assertions": total_assertions,
        "assertions_passed": assertions_passed,
        "assertion_pass_rate": (assertions_passed / total_assertions) if total_assertions else 0.0,
        "results": test_results,
        "error": None,
    }
    write_instance_result(output_dir, result)
    return result


def write_summary(output_dir: Path, all_results: list[dict], elapsed: float) -> dict:
    """Write summary.json with aggregate patch replay stats."""
    total_tests = sum(result.get("num_tests", 0) for result in all_results)
    total_passed = sum(result.get("num_tests_passed", 0) for result in all_results)
    total_errors = sum(1 for result in all_results if result.get("error"))
    total_assertions = sum(result.get("total_assertions", 0) for result in all_results)
    assertions_passed = sum(result.get("assertions_passed", 0) for result in all_results)

    repo_summary: dict[str, dict] = {}
    for result in all_results:
        repo = result["repo"]
        if repo not in repo_summary:
            repo_summary[repo] = {
                "repo": repo,
                "instances": 0,
                "tests": 0,
                "tests_passed": 0,
                "assertions": 0,
                "assertions_passed": 0,
            }

        repo_data = repo_summary[repo]
        repo_data["instances"] += 1
        repo_data["tests"] += result.get("num_tests", 0)
        repo_data["tests_passed"] += result.get("num_tests_passed", 0)
        repo_data["assertions"] += result.get("total_assertions", 0)
        repo_data["assertions_passed"] += result.get("assertions_passed", 0)

    for repo_data in repo_summary.values():
        tests = repo_data["tests"]
        repo_data["test_pass_rate"] = (
            repo_data["tests_passed"] / tests if tests else 0.0
        )
        asserts = repo_data["assertions"]
        repo_data["assertion_pass_rate"] = (
            repo_data["assertions_passed"] / asserts if asserts else 0.0
        )

    summary = {
        "total_instances": len(all_results),
        "total_tests": total_tests,
        "total_tests_passed": total_passed,
        "total_errors": total_errors,
        "overall_test_pass_rate": (total_passed / total_tests) if total_tests else 0.0,
        "total_assertions": total_assertions,
        "assertions_passed": assertions_passed,
        "assertion_pass_rate": (assertions_passed / total_assertions) if total_assertions else 0.0,
        "elapsed_seconds": elapsed,
        "repo_summary": list(repo_summary.values()),
        "instance_results": [
            {
                "instance_id": result["instance_id"],
                "repo": result["repo"],
                "patch_applied": result.get("patch_applied", False),
                "num_tests": result.get("num_tests", 0),
                "num_tests_passed": result.get("num_tests_passed", 0),
                "test_pass_rate": result.get("test_pass_rate", 0.0),
                "total_assertions": result.get("total_assertions", 0),
                "assertions_passed": result.get("assertions_passed", 0),
                "error": result.get("error"),
            }
            for result in all_results
        ],
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay stored agent patches in Docker and run verified tests"
    )
    parser.add_argument(
        "--dataset-file",
        type=str,
        default=DEFAULT_DATASET_FILE,
        help=f"Dataset JSONL file (default: {DEFAULT_DATASET_FILE})",
    )
    parser.add_argument(
        "--patch-dir",
        type=str,
        default=DEFAULT_PATCH_DIR,
        help=f"Combined patch results directory (default: {DEFAULT_PATCH_DIR})",
    )
    parser.add_argument(
        "--testgen-dir",
        type=str,
        default=DEFAULT_TESTGEN_DIR,
        help=f"Combined testgen results directory (default: {DEFAULT_TESTGEN_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--docker-image-map-file",
        type=str,
        default=DEFAULT_DOCKER_IMAGE_MAP_FILE,
        help=(
            "CSV mapping instance_id -> selected_image. When an instance is in "
            "the map its image is used directly, avoiding live Docker probing "
            f"(default: {DEFAULT_DOCKER_IMAGE_MAP_FILE})"
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=30,
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
    patch_dir = Path(args.patch_dir)
    testgen_dir = Path(args.testgen_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = not args.no_resume

    if not dataset_file.exists():
        logger.error("Dataset file not found: %s", dataset_file)
        sys.exit(1)

    docker_image_map = load_docker_image_map(Path(args.docker_image_map_file))
    logger.info(
        "Loaded %d image mappings from %s",
        len(docker_image_map),
        args.docker_image_map_file,
    )

    all_dataset = load_dataset_instances(dataset_file)
    logger.info("Loaded %d instances from %s", len(all_dataset), dataset_file)

    if args.repo:
        all_dataset = [instance for instance in all_dataset if instance["repo"] == args.repo]
        logger.info("Filtered to %d instances for repo %s", len(all_dataset), args.repo)

    if args.limit and len(all_dataset) > args.limit:
        all_dataset = all_dataset[: args.limit]
        logger.info("Limited to %d instances", len(all_dataset))

    if not all_dataset:
        logger.error("No instances to process.")
        sys.exit(1)

    all_results: list[dict] = []
    to_process: list[tuple[dict, dict, dict, str]] = []

    for instance in all_dataset:
        instance_id = instance["instance_id"]

        if resume:
            existing = load_existing_result(output_dir, instance_id)
            if existing is not None:
                logger.info("Skipping (already done): %s", instance_id)
                all_results.append(existing)
                continue

        docker_image = docker_image_map.get(instance_id) or resolve_docker_image(instance_id)

        patch_result = load_combined_result(patch_dir, instance_id)
        if patch_result is None:
            all_results.append(
                make_stub_result(instance, error="No combined patch result found")
            )
            continue

        testgen_result = load_combined_result(testgen_dir, instance_id)
        if testgen_result is None:
            all_results.append(
                make_stub_result(instance, error="No combined testgen result found")
            )
            continue

        to_process.append((instance, patch_result, testgen_result, docker_image))

    if not to_process:
        summary = write_summary(output_dir, all_results, 0.0)
        logger.info(
            "Summary: %d instances, %d/%d tests passed (%.1f%%)",
            summary["total_instances"],
            summary["total_tests_passed"],
            summary["total_tests"],
            summary["overall_test_pass_rate"] * 100,
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

    def _process_one(
        instance: dict,
        patch_result: dict,
        testgen_result: dict,
        docker_image: str,
    ) -> dict:
        return process_instance(
            instance=instance,
            patch_result=patch_result,
            testgen_result=testgen_result,
            output_dir=output_dir,
            docker_image=docker_image,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_instance = {
            executor.submit(_process_one, instance, patch_result, testgen_result, docker_image): instance
            for instance, patch_result, testgen_result, docker_image in to_process
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
                "[%d/%d] Completed %s: %d/%d tests passed",
                count,
                len(to_process),
                instance["instance_id"],
                result.get("num_tests_passed", 0),
                result.get("num_tests", 0),
            )

            if count % 10 == 0:
                with lock:
                    elapsed_so_far = time.time() - start_time
                    summary = write_summary(output_dir, list(all_results), elapsed_so_far)
                logger.info(
                    "Progress: %d/%d instances, %d/%d tests passed (%.1f%%)",
                    len(all_results),
                    len(all_dataset),
                    summary["total_tests_passed"],
                    summary["total_tests"],
                    summary["overall_test_pass_rate"] * 100,
                )

    total_elapsed = time.time() - start_time
    summary = write_summary(output_dir, all_results, total_elapsed)
    logger.info(
        "=== DONE === %d instances, %d/%d tests passed (%.1f%%), %d errors, %.0fs elapsed",
        summary["total_instances"],
        summary["total_tests_passed"],
        summary["total_tests"],
        summary["overall_test_pass_rate"] * 100,
        summary["total_errors"],
        total_elapsed,
    )
    logger.info("Summary: %s", output_dir / "summary.json")


if __name__ == "__main__":
    main()
