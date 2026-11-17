#!/usr/bin/env python3
"""Per-instance agentic test generation with Qwen Code.

Uses one Qwen Code invocation inside a Docker container to generate validation
tests for all selected review comments in an instance. Generated tests and
result.json remain compatible with run_testgen.py outputs, while Qwen artifacts
are saved similarly to the agent resolution runner.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline import diff_analyzer, test_generator, test_runner
from pipeline.agent_resolver import (
    get_qwen_auth_config,
    get_qwen_mounts,
    invoke_qwen_in_container,
    setup_qwen_in_container,
    write_agent_trajectory,
)
from pipeline.llm_client import LLMUsage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = ""
DEFAULT_DATASET_FILE = "dataset/instances.jsonl"
DEFAULT_OUTPUT_DIR = "results_agent_testgen"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"
DEFAULT_QWEN_SETTINGS = Path.home() / ".qwen" / "settings.json"
EXECUTABLE_LANGUAGES = {"python", "javascript", "typescript", "go"}


def load_dataset_instance(dataset_file: Path, instance_id: str) -> dict | None:
    """Load a single instance from a dataset JSONL file."""
    with dataset_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            instance = json.loads(line)
            if instance["instance_id"] == instance_id:
                return instance
    return None


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


def load_comment_selection_file(comments_file: Path) -> dict[str, set[int]]:
    """Load comment targets from a CSV with instance_id/comment_index columns."""
    if not comments_file.exists():
        raise FileNotFoundError(f"Comments file not found: {comments_file}")

    selections: dict[str, set[int]] = {}
    with comments_file.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"instance_id", "comment_index"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                "Comments file must contain 'instance_id' and 'comment_index' columns"
            )

        for row in reader:
            instance_id = (row.get("instance_id") or "").strip()
            comment_index_raw = (row.get("comment_index") or "").strip()
            if not instance_id or not comment_index_raw:
                continue
            try:
                comment_index = int(comment_index_raw)
            except ValueError as e:
                raise ValueError(
                    f"Invalid comment_index '{comment_index_raw}' for instance "
                    f"{instance_id}"
                ) from e
            selections.setdefault(instance_id, set()).add(comment_index)
    return selections


def _write_artifact(
    artifact_dir: Path,
    filename: str,
    content: str,
    artifacts: dict[str, str],
) -> str:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / filename
    path.write_text(content or "", encoding="utf-8")
    artifacts[filename] = str(path)
    return str(path)


def _trajectory_step(phase: str, **details: object) -> dict:
    return {
        "phase": phase,
        "timestamp": time.time(),
        **details,
    }


def _build_prompt_with_environment_notes(
    context: diff_analyzer.CommentContext,
    comment: dict,
    repo: str,
    comment_type: str,
    language: str,
    environment_notes: str,
) -> str:
    context = diff_analyzer.CommentContext(
        file_path=context.file_path,
        before_code=context.before_code,
        diff_hunk=_mark_commented_line_in_diff(context.diff_hunk, comment),
        before_patch_lines=context.before_patch_lines,
        comment_text=context.comment_text,
    )
    prompt = test_generator._build_prompt(context, repo, comment_type, language)
    prompt = _remove_large_context_sections(prompt)
    if environment_notes:
        prompt += f"\n\n## Environment Pre-flight Results\n{environment_notes}\n"
    return prompt


def _mark_commented_line_in_diff(diff_hunk: str, comment: dict) -> str:
    """Insert a visible marker before the diff line the review comment targets."""
    target_line = comment.get("line") or comment.get("original_line")
    if target_line is None:
        return diff_hunk
    try:
        target_line = int(target_line)
    except (TypeError, ValueError):
        return diff_hunk

    start_line = comment.get("start_line") or comment.get("original_start_line")
    try:
        start_line = int(start_line) if start_line is not None else target_line
    except (TypeError, ValueError):
        start_line = target_line

    old_lineno = None
    new_lineno = None
    marked_lines = []
    inserted = False

    for line in diff_hunk.splitlines():
        hunk_match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk_match:
            old_lineno = int(hunk_match.group(1))
            new_lineno = int(hunk_match.group(2))
            marked_lines.append(line)
            continue

        current_new_lineno = None
        current_old_lineno = None
        if new_lineno is not None and old_lineno is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_new_lineno = new_lineno
                new_lineno += 1
            elif line.startswith("-") and not line.startswith("---"):
                current_old_lineno = old_lineno
                old_lineno += 1
            elif line.startswith(" "):
                current_old_lineno = old_lineno
                current_new_lineno = new_lineno
                old_lineno += 1
                new_lineno += 1

        in_comment_range = (
            current_new_lineno is not None
            and start_line <= current_new_lineno <= target_line
        )
        if in_comment_range and not inserted:
            marked_lines.append(
                f">>> REVIEW COMMENT ATTACHED HERE "
                f"(lines {start_line}-{target_line})"
            )
            inserted = True
        marked_lines.append(line)

    if not inserted:
        marked_lines.append(
            f">>> REVIEW COMMENT LOCATION: lines {start_line}-{target_line}"
        )
    return "\n".join(marked_lines)


def _remove_large_context_sections(prompt: str) -> str:
    """Drop bulky per-comment context duplicated across batched agent prompts."""
    return re.sub(
        (
            r"\n## Relevant current diff context\n```[^\n]*\n.*?\n```\n\n"
            r"## Full file currently under review\n```[^\n]*\n.*?\n```\n"
        ),
        "\n",
        prompt,
        flags=re.DOTALL,
    )


def _build_batch_prompt(comment_jobs: list[dict]) -> str:
    sections = []
    for job in comment_jobs:
        sections.append(
            f"""### Comment {job["comment_index"]}
Target test file: /workspace/{job["test_filename"]}
Language: {job["language"]}

{job["prompt"]}

If you generate a test for this comment, write the final code to:
/workspace/{job["test_filename"]}
"""
        )

    comment_sections = "\n\n".join(sections)
    return f"""You are Qwen Code running inside the repository at /workspace.

Generate validation tests for all review comments in this instance.

Rules:
- Keep the same test-generation requirements, constraints, and output expectations from each embedded per-comment prompt.
- Follow the execution-environment and language-specific test rules from each embedded prompt exactly, including framework choice, runnable command expectations, absolute `/workspace/...` file paths, and clean execution requirements.
- Do not modify existing repository source files.
- Write one generated test file per comment using the exact target path shown in that comment section.
- If a comment cannot produce a valid executable test, do not invent a placeholder test. Leave its target file absent and mention the reason in your final summary.
- Keep tests focused and self-contained.

For each comment below:
- Read the target path.
- Follow the embedded prompt for that comment.
- Write only that comment's generated test code to the target path.

## Comments To Generate Tests For

{comment_sections}

## Final Response
Return a concise summary listing each comment index, target test file, and whether you wrote the file.
"""



def _python_environment_notes(
    session: DockerContainerSession,
    head_commit: str,
    file_path: str,
) -> str:
    module_path = file_path.replace("/", ".").replace(".py", "")
    probe = session.run_command(
        f"git checkout --force {head_commit} --quiet 2>/dev/null; "
        f"python -c \"import {module_path}\" 2>&1",
        timeout=30,
    )
    if probe.returncode != 0:
        error_snippet = (probe.stdout + probe.stderr).strip()[-300:]
        return (
            f"WARNING: `import {module_path}` FAILS in this environment.\n"
            f"Error: {error_snippet}\n\n"
            "You MUST use source file inspection instead of importing the module. "
            f"Read the file with `open('/workspace/{file_path}').read()` "
            "and check for the specific code pattern that changed in the diff. "
            f"Do NOT attempt to import {module_path} or any of its parent packages."
        )
    return (
        f"`import {module_path}` works. Prefer functional tests that "
        "import and exercise the actual code."
    )


def _make_error_result(
    comment_index: int,
    comment: dict,
    comment_type: str,
    language: str,
    error: str,
    trajectory_path: str | None = None,
) -> dict:
    trajectory = None
    if trajectory_path:
        trajectory = {"format": "agent_stdout", "path": trajectory_path}
    result = {
        "comment_index": comment_index,
        "comment_text": comment["text"],
        "comment_type": comment_type,
        "language": language,
        "test_file": None,
        "test_code": None,
        "error": error,
        "current_passed": None,
        "current_output": "",
        "expected_failure_observed": False,
        "success": False,
        "assessment": {
            "ground_truth_patch_passed": None,
            "ground_truth_patch_output": "",
            "current_fails_and_patch_passes": None,
        },
        "attempts_used": 0,
        "usage": LLMUsage().to_dict(),
    }
    if trajectory is not None:
        result["trajectory"] = trajectory
    return result


def _collect_generated_tests_diff(
    session: DockerContainerSession,
    test_filenames: list[str],
) -> str:
    parts = []
    for filename in test_filenames:
        path = f"/workspace/{filename}"
        exists = session.run_command(f"test -f {path}", timeout=10)
        if exists.returncode != 0:
            continue
        diff = session.run_command(
            f"git diff --no-index -- /dev/null {path} || true",
            timeout=30,
        )
        parts.append(diff.stdout)
        if diff.stderr:
            parts.append(diff.stderr)
    return "\n".join(part for part in parts if part)


def _copy_generated_test(
    session: DockerContainerSession,
    container_filename: str,
    local_path: Path,
) -> bool:
    exists = session.run_command(f"test -f /workspace/{container_filename}", timeout=10)
    if exists.returncode != 0:
        return False
    session.copy_from(f"/workspace/{container_filename}", local_path)
    return True


def process_instance(
    instance: dict,
    output_dir: Path,
    model: str,
    docker_image: str,
    qwen_settings_path: Path,
    selected_comment_indices: set[int] | None = None,
    skip_execution: bool = False,
    dry_run: bool = False,
) -> dict:
    """Generate validation tests for one instance using one Qwen invocation."""
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    all_comments = instance["reference_review_comments"]
    head_commit = instance["commit_to_review"]["head_commit"]
    merged_commit = instance["merged_commit"]
    patch_to_review = instance["commit_to_review"]["patch_to_review"]

    if selected_comment_indices is None:
        indexed_comments = list(enumerate(all_comments))
    else:
        indexed_comments = [
            (comment_index, comment)
            for comment_index, comment in enumerate(all_comments)
            if comment_index in selected_comment_indices
        ]

    logger.info(
        "Processing instance: %s (%d selected comments)",
        instance_id,
        len(indexed_comments),
    )

    instance_dir = output_dir / instance_id.replace("/", "__")
    instance_dir.mkdir(parents=True, exist_ok=True)

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-agent-testgen-{safe_name}"
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

    artifacts: dict[str, str] = {}
    trajectory: list[dict] = []
    comment_results: list[dict] = []
    comment_jobs: list[dict] = []

    def _persist_trajectory() -> str | None:
        return write_agent_trajectory(
            artifact_dir=instance_dir,
            instance=instance,
            model=model,
            agent="qwen-code",
            raw_events=trajectory,
            artifacts=artifacts,
            comment_indices=[job["comment_index"] for job in comment_jobs],
        )

    def _record_agent_stream_event(event: dict) -> None:
        trajectory.append(_trajectory_step("agent_stream_event", event=event))
        _persist_trajectory()

    try:
        session.start()
        logger.info("Started container %s (image: %s)", container_name, docker_image)
        setup_qwen_in_container(session)

        def get_file_fn(commit, filepath):
            result = session.run_command(
                ["git", "show", f"{commit}:{filepath}"],
                timeout=30,
            )
            if result.returncode != 0:
                return ""
            return result.stdout

        reset_command = f"git checkout --force {head_commit} && git clean -fd --quiet"
        started = time.time()
        reset_result = session.run_command(reset_command, timeout=120)
        trajectory.append(
            _trajectory_step(
                "setup",
                action="reset_to_head_commit",
                command=reset_command,
                returncode=reset_result.returncode,
                stdout=reset_result.stdout,
                stderr=reset_result.stderr,
                elapsed_seconds=time.time() - started,
            )
        )
        if reset_result.returncode != 0:
            error = f"git checkout failed: {reset_result.stderr[:500]}"
            for i, comment in indexed_comments:
                language = (
                    test_generator.detect_language(comment["path"])
                    or test_generator.DEFAULT_LANGUAGE
                )
                comment_results.append(
                    _make_error_result(i, comment, "unknown", language, error)
                )
        else:
            for position, (i, comment) in enumerate(indexed_comments):
                logger.info(
                    "  Preparing comment %d/%d: [%s] %s",
                    position + 1,
                    len(indexed_comments),
                    comment["path"],
                    comment["text"][:80],
                )
                language = (
                    test_generator.detect_language(comment["path"])
                    or test_generator.DEFAULT_LANGUAGE
                )
                comment_type = test_generator.classify_comment(
                    comment["text"], comment.get("diff_hunk", "")
                )

                if language not in EXECUTABLE_LANGUAGES:
                    comment_results.append(
                        _make_error_result(
                            i,
                            comment,
                            comment_type,
                            language,
                            f"Language '{language}' not supported for test execution",
                        )
                    )
                    continue

                context = diff_analyzer.extract_comment_context(
                    comment=comment,
                    patch_to_review=patch_to_review,
                    get_file_fn=get_file_fn,
                    head_commit=head_commit,
                )
                environment_notes = ""
                if language == "python":
                    environment_notes = _python_environment_notes(
                        session, head_commit, comment["path"]
                    )

                test_ext = test_generator.get_test_file_ext(language)
                test_filename = f"test_review_comment_{i}{test_ext}"
                prompt = _build_prompt_with_environment_notes(
                    context=context,
                    comment=comment,
                    repo=repo,
                    comment_type=comment_type,
                    language=language,
                    environment_notes=environment_notes,
                )
                comment_jobs.append(
                    {
                        "comment_index": i,
                        "comment": comment,
                        "comment_type": comment_type,
                        "language": language,
                        "path": comment["path"],
                        "before_code": context.before_code,
                        "test_filename": test_filename,
                        "prompt": prompt,
                    }
                )

            if comment_jobs:
                batch_prompt = _build_batch_prompt(comment_jobs)
                prompt_path = _write_artifact(
                    instance_dir, "prompt.txt", batch_prompt, artifacts
                )
                trajectory.append(
                    _trajectory_step(
                        "agent_prompt",
                        prompt=batch_prompt,
                        artifact_path=prompt_path,
                        num_comments=len(comment_jobs),
                    )
                )
                if dry_run:
                    trajectory.append(
                        _trajectory_step(
                            "dry_run",
                            message="Stopped after prompt generation before Qwen invocation.",
                        )
                    )
                    trajectory_path = _persist_trajectory()
                    for job in comment_jobs:
                        comment_results.append(
                            _make_error_result(
                                job["comment_index"],
                                job["comment"],
                                job["comment_type"],
                                job["language"],
                                "Dry run: prompt generated; Qwen was not invoked",
                                trajectory_path,
                            )
                        )
                    logger.info("Dry run complete: prompt saved to %s", prompt_path)
                    return _finalize_result(
                        instance_id=instance_id,
                        repo=repo,
                        model=model,
                        indexed_comments=indexed_comments,
                        comment_results=comment_results,
                        artifacts=artifacts,
                        instance_dir=instance_dir,
                    )

                logger.info(
                    "  Invoking Qwen Code once for %d comment(s)...",
                    len(comment_jobs),
                )
                started = time.time()
                agent_stdout, agent_stderr, agent_rc = invoke_qwen_in_container(
                    session,
                    batch_prompt,
                    model,
                    auth_type=qwen_auth_type,
                    on_stream_event=_record_agent_stream_event,
                )
                stdout_path = _write_artifact(
                    instance_dir, "qwen_stdout.txt", agent_stdout, artifacts
                )
                stderr_path = _write_artifact(
                    instance_dir, "qwen_stderr.txt", agent_stderr, artifacts
                )
                trajectory.append(
                    _trajectory_step(
                        "agent_response",
                        returncode=agent_rc,
                        stdout=agent_stdout,
                        stderr=agent_stderr,
                        stdout_artifact_path=stdout_path,
                        stderr_artifact_path=stderr_path,
                        elapsed_seconds=time.time() - started,
                    )
                )
                _persist_trajectory()

                generated_diff = _collect_generated_tests_diff(
                    session,
                    [job["test_filename"] for job in comment_jobs],
                )
                diff_path = _write_artifact(
                    instance_dir, "generated_tests.diff", generated_diff, artifacts
                )
                trajectory.append(
                    _trajectory_step(
                        "generated_tests_diff",
                        artifact_path=diff_path,
                        diff_chars=len(generated_diff),
                    )
                )

                trajectory_path = _persist_trajectory()

                for job in comment_jobs:
                    i = job["comment_index"]
                    comment = job["comment"]
                    language = job["language"]
                    comment_type = job["comment_type"]
                    test_filename = job["test_filename"]
                    test_file = (instance_dir / test_filename).resolve()
                    test_file_rel = str(Path(instance_dir.name) / test_filename)
                    test_copied = _copy_generated_test(
                        session, test_filename, test_file
                    )
                    if not test_copied:
                        comment_results.append(
                            _make_error_result(
                                i,
                                comment,
                                comment_type,
                                language,
                                "Agent did not write expected test file",
                                trajectory_path,
                            )
                        )
                        continue

                    test_code = test_file.read_text(encoding="utf-8")
                    syntax_ok = test_generator.validate_test_syntax(
                        test_code, language
                    )
                    if not syntax_ok:
                        comment_results.append(
                            {
                                **_make_error_result(
                                    i,
                                    comment,
                                    comment_type,
                                    language,
                                    "Generated test failed syntax/structure validation",
                                    trajectory_path,
                                ),
                                "test_file": test_file_rel,
                                "test_code": test_code,
                                "attempts_used": 1,
                            }
                        )
                        continue

                    if skip_execution:
                        result_entry = {
                            "comment_index": i,
                            "comment_text": comment["text"],
                            "comment_type": comment_type,
                            "language": language,
                            "test_file": test_file_rel,
                            "test_code": test_code,
                            "current_passed": None,
                            "current_output": "",
                            "expected_failure_observed": None,
                            "success": None,
                            "assessment": {
                                "ground_truth_patch_passed": None,
                                "ground_truth_patch_output": "",
                                "current_fails_and_patch_passes": None,
                            },
                            "attempts_used": 1,
                            "usage": LLMUsage().to_dict(),
                            "trajectory": {
                                "format": "agent_stdout",
                                "path": trajectory_path,
                            },
                        }
                        comment_results.append(result_entry)
                        continue

                    current = test_runner.run_test_current_version_docker(
                        session=session,
                        test_file=test_file,
                        head_commit=head_commit,
                        comment_index=i,
                        language=language,
                    )
                    patched = test_runner.run_test_ground_truth_patch_docker(
                        session=session,
                        test_file=test_file,
                        merged_commit=merged_commit,
                        comment_index=i,
                        language=language,
                    )
                    trajectory.append(
                        _trajectory_step(
                            "test_validation",
                            comment_index=i,
                            test_file=test_filename,
                            language=language,
                            current_passed=current.current_passed,
                            current_output=current.current_output,
                            expected_failure_observed=current.expected_failure_observed,
                            ground_truth_patch_passed=patched.patched_passed,
                            ground_truth_patch_output=patched.patched_output,
                        )
                    )
                    trajectory_path = _persist_trajectory()
                    result_entry = {
                        "comment_index": i,
                        "comment_text": comment["text"],
                        "comment_type": comment_type,
                        "language": language,
                        "test_file": test_file_rel,
                        "test_code": test_code,
                        "current_passed": current.current_passed,
                        "current_output": current.current_output,
                        "expected_failure_observed": current.expected_failure_observed,
                        "success": current.expected_failure_observed,
                        "assessment": {
                            "ground_truth_patch_passed": patched.patched_passed,
                            "ground_truth_patch_output": patched.patched_output,
                            "current_fails_and_patch_passes": (
                                current.expected_failure_observed
                                and patched.patched_passed
                            ),
                        },
                        "attempts_used": 1,
                        "usage": LLMUsage().to_dict(),
                        "trajectory": {
                            "format": "agent_stdout",
                            "path": trajectory_path,
                        },
                    }
                    comment_results.append(result_entry)

    finally:
        session.remove(force=True)
        logger.info("Removed container %s", container_name)

    return _finalize_result(
        instance_id=instance_id,
        repo=repo,
        model=model,
        indexed_comments=indexed_comments,
        comment_results=comment_results,
        artifacts=artifacts,
        instance_dir=instance_dir,
    )


def _finalize_result(
    instance_id: str,
    repo: str,
    model: str,
    indexed_comments: list[tuple[int, dict]],
    comment_results: list[dict],
    artifacts: dict[str, str],
    instance_dir: Path,
    result_filename: str = "result.json",
) -> dict:
    sort_order = {i: position for position, (i, _) in enumerate(indexed_comments)}
    comment_results.sort(key=lambda result: sort_order.get(result["comment_index"], 0))
    tested = [r for r in comment_results if r["success"] is not None]
    expected_failures = sum(1 for r in tested if r["success"])
    expected_failure_rate = expected_failures / len(tested) if tested else 0.0

    result = {
        "instance_id": instance_id,
        "repo": repo,
        "agent": "qwen-code",
        "model": model,
        "usage": LLMUsage().to_dict(),
        "num_comments": len(indexed_comments),
        "results": comment_results,
        "overall_expected_failure_rate": expected_failure_rate,
        "trajectory": {
            "format": "agent_stdout",
            "path": artifacts.get("trajectory.json"),
        },
        "artifacts": artifacts,
    }

    result_file = instance_dir / result_filename
    result_file.write_text(json.dumps(result, indent=2, default=str))
    logger.info(
        "Result saved to %s (expected-failure rate: %.1f%%)",
        result_file,
        expected_failure_rate * 100,
    )
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate review-time validation tests with Qwen Code in Docker"
    )
    parser.add_argument("--instance-id", type=str, required=True)
    parser.add_argument(
        "--dataset-file",
        type=str,
        default=DEFAULT_DATASET_FILE,
        help=f"Dataset JSONL file (default: {DEFAULT_DATASET_FILE})",
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
        help="Qwen model to use (default: use Qwen configured default)",
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
        "--comments-file",
        type=str,
        default=None,
        help="CSV of comment targets with instance_id and comment_index columns",
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

    args = parser.parse_args()
    dataset_file = Path(args.dataset_file)
    output_dir = Path(args.output_dir)
    docker_image_map_file = Path(args.docker_image_map)
    qwen_settings_path = Path(args.qwen_settings)
    output_dir.mkdir(parents=True, exist_ok=True)

    instance = load_dataset_instance(dataset_file, args.instance_id)
    if instance is None:
        logger.error("Instance %s not found in %s", args.instance_id, dataset_file)
        sys.exit(1)

    selected_comment_indices = None
    if args.comments_file:
        selections = load_comment_selection_file(Path(args.comments_file))
        selected_comment_indices = selections.get(args.instance_id, set())

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

    process_instance(
        instance=instance,
        output_dir=output_dir,
        model=args.model,
        docker_image=docker_image,
        qwen_settings_path=qwen_settings_path,
        selected_comment_indices=selected_comment_indices,
        skip_execution=args.skip_execution,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
