"""Validation-test guided agent resolution of code review comments.

This resolver uses generated validation tests as the in-loop repair signal. It
first runs the copied validation tests against the current code under review,
then asks Qwen Code to revise any weak validation tests and fix the production
code so the validation suite passes.
"""

from __future__ import annotations

import logging
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline.agent_resolver import (
    _trajectory_step,
    _write_artifact,
    build_test_command,
    invoke_qwen_in_container,
    write_agent_trajectory,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResolution:
    """Result of resolving one comment with generated validation tests."""

    comment_index: int
    comment_text: str
    file_path: str
    language: str
    validation_test_file: str
    validation_initial_passed: bool
    validation_initial_output: str
    validation_final_passed: bool
    validation_final_output: str
    expected_failure_observed: bool
    initial_unexpected_pass: bool
    validation_test_revised: bool
    resolved: bool
    agent_diff: str
    validation_test_diff: str
    error: str | None

    def to_dict(self) -> dict:
        d = asdict(self)
        # resolved / test_passed are groundtruth-assessment signals and must not
        # appear in the per-comment validation results; they live only in the
        # groundtruth_assessment block of result.json.
        d.pop("resolved", None)
        return d


@dataclass
class ValidationResolveResult:
    """Batch validation-guided result plus execution trajectory."""

    resolutions: list[ValidationResolution]
    trajectory: list[dict]
    artifacts: dict[str, str]


def _copy_validation_test(
    session: DockerContainerSession,
    *,
    test_code: str,
    test_filename: str,
    source_test_path: Path | None,
) -> str:
    """Copy a validation test to /workspace and keep an original copy."""
    container_test_path = f"/workspace/{test_filename}"
    original_path = f"/tmp/original_validation_tests/{test_filename}"
    session.run_command("mkdir -p /tmp/original_validation_tests", timeout=10)

    if not test_code and source_test_path is None:
        session.run_command(
            f"mkdir -p {Path(original_path).parent} && : > {original_path}",
            timeout=10,
        )
        return container_test_path

    if source_test_path is not None and source_test_path.exists():
        session.copy_to(source_test_path, container_test_path)
        session.copy_to(source_test_path, original_path)
        return container_test_path

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f"_{test_filename}", delete=False
    ) as handle:
        handle.write(test_code)
        local_test_path = Path(handle.name)
    try:
        session.copy_to(local_test_path, container_test_path)
        session.copy_to(local_test_path, original_path)
    finally:
        local_test_path.unlink(missing_ok=True)
    return container_test_path


def _run_existing_validation_test(
    session: DockerContainerSession,
    *,
    test_filename: str,
    language: str,
) -> dict:
    """Run an already-copied validation test from /workspace."""
    container_test_path = f"/workspace/{test_filename}"
    run_cmd = build_test_command(container_test_path, language)
    if run_cmd is None:
        return {
            "passed": False,
            "output": f"Execution not supported for language: {language}",
            "command": None,
            "returncode": None,
            "container_test_path": container_test_path,
        }

    started = time.time()
    result = session.run_command(run_cmd, timeout=120)
    combined = (result.stdout + "\n" + result.stderr).strip()
    return {
        "passed": result.returncode == 0,
        "output": combined,
        "command": run_cmd,
        "returncode": result.returncode,
        "container_test_path": container_test_path,
        "elapsed_seconds": time.time() - started,
    }


def _capture_validation_test_diff(
    session: DockerContainerSession,
    test_filenames: list[str],
) -> str:
    """Return a diff between copied validation tests and their post-agent state."""
    if not test_filenames:
        return ""
    files_literal = repr(test_filenames)
    command = (
        "rm -rf /tmp/current_validation_tests && "
        "mkdir -p /tmp/current_validation_tests && "
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        f"files = {files_literal}\n"
        "for name in files:\n"
        "    src = Path('/workspace') / name\n"
        "    dst = Path('/tmp/current_validation_tests') / name\n"
        "    if src.exists():\n"
        "        dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')\n"
        "PY\n"
        "diff -ru /tmp/original_validation_tests /tmp/current_validation_tests || true"
    )
    result = session.run_command(command, timeout=30)
    return (result.stdout + "\n" + result.stderr).strip()


def build_validation_prompt(
    *,
    comments: list[dict],
    validation_tests: dict[int, dict],
    initial_results: dict[int, dict],
    patch_to_review: str,
    repo: str,
) -> str:
    """Build a validation-test guided repair prompt."""
    sections = []
    for ordinal, comment in enumerate(comments, 1):
        comment_index = comment["comment_index"]
        test = validation_tests[comment_index]
        initial = initial_results[comment_index]
        initial_status = "PASSED" if initial["passed"] else "FAILED"
        validation_note = (
            "This validation test file did not exist before the agent run. "
            "Create it at the named path, make it fail on the current unaddressed "
            "issue, then fix the production code so it passes."
            if test.get("generated_by_agent")
            else "This validation test was generated before the agent run."
        )
        sections.append(
            f"### Comment {ordinal} (dataset index {comment_index})\n"
            f"**File:** `{comment['path']}`\n\n"
            f"**Diff hunk being reviewed:**\n"
            f"```\n{comment.get('diff_hunk', '')}\n```\n\n"
            f"**Reviewer says:**\n{comment['text']}\n\n"
            f"**Validation test:** `/workspace/{test['test_filename']}`\n\n"
            f"**Validation test note:** {validation_note}\n\n"
            f"**Initial validation result on current code:** {initial_status}\n"
            f"**Command:** `{initial.get('command')}`\n"
            f"**Output:**\n```\n{initial.get('output', '')}\n```"
        )

    comments_block = "\n\n---\n\n".join(sections)

    return f"""You are resolving code review comments on the repository `{repo}`.

You have generated validation tests copied into `/workspace`.
They are repair-time validation signals. Each comment section below names the
exact validation test file for that comment, for example
`/workspace/test_review_comment_N.py`. Inspect and run those named files when
validating your changes.

## Review Comments And Validation Results

{comments_block}

## Full PR Diff
```
{patch_to_review}
```

## Instructions
1. Read each review comment and its validation test path.
2. If a validation test file is missing, create it at the named `/workspace/...`
   path. The new test should capture the reviewer feedback and fail before the
   production fix.
3. Run the validation tests on the current code when they already exist.
4. If a validation test PASSED on the current code before any repair, inspect and
   modify that validation test so it actually captures the reviewer feedback and
   would fail on the unaddressed issue. If the validation tests do not exist in the workspace, create them.
5. Fix the production code to address ALL reviewer feedback.
6. Re-run the validation tests while working and make them pass.
7. Keep changes minimal. Do not use these validation tests as evidence of final
   ground-truth correctness; they are only a repair aid.
"""


def _make_resolution(
    *,
    comment_index: int,
    test: dict,
    initial_result: dict | None,
    final_result: dict | None,
    agent_diff: str,
    validation_test_diff: str,
    error: str | None,
) -> ValidationResolution:
    comment = test["comment"]
    initial_passed = bool(initial_result and initial_result.get("passed"))
    final_passed = bool(final_result and final_result.get("passed"))
    validation_test_revised = (
        test["test_filename"] in validation_test_diff
        or bool(test.get("generated_by_agent"))
    )
    expected_failure_observed = not initial_passed if initial_result else False
    initial_unexpected_pass = initial_passed if initial_result else False
    production_changed = bool(agent_diff.strip())
    resolved = (
        final_passed
        and production_changed
        and (expected_failure_observed or validation_test_revised)
    )
    return ValidationResolution(
        comment_index=comment_index,
        comment_text=comment.get("text", ""),
        file_path=comment.get("path", ""),
        language=test["language"],
        validation_test_file=test["test_filename"],
        validation_initial_passed=initial_passed,
        validation_initial_output=str((initial_result or {}).get("output", "")),
        validation_final_passed=final_passed,
        validation_final_output=str((final_result or {}).get("output", "")),
        expected_failure_observed=expected_failure_observed,
        initial_unexpected_pass=initial_unexpected_pass,
        validation_test_revised=validation_test_revised,
        resolved=resolved,
        agent_diff=agent_diff,
        validation_test_diff=validation_test_diff,
        error=error,
    )


def resolve_instance_with_validation_tests(
    *,
    instance: dict,
    validation_tests: dict[int, dict],
    session: DockerContainerSession,
    model: str,
    qwen_auth_type: str | None = None,
    artifact_dir: Path | None = None,
) -> ValidationResolveResult:
    """Resolve comments using generated validation tests inside Docker."""
    head_commit = instance["commit_to_review"]["head_commit"]
    repo = instance["repo"]
    patch_to_review = instance["commit_to_review"]["patch_to_review"]
    ordered_indices = sorted(validation_tests.keys())
    comments_for_prompt = []
    trajectory: list[dict] = []
    artifacts: dict[str, str] = {}
    initial_results: dict[int, dict] = {}
    final_results: dict[int, dict] = {}
    agent_diff = ""
    validation_test_diff = ""

    def _persist_trajectory() -> None:
        write_agent_trajectory(
            artifact_dir=artifact_dir,
            instance=instance,
            model=model,
            agent="qwen-code-validation-test",
            raw_events=trajectory,
            artifacts=artifacts,
            comment_indices=ordered_indices,
        )

    def _record_agent_stream_event(event: dict) -> None:
        trajectory.append(_trajectory_step("agent_stream_event", event=event))
        _persist_trajectory()

    def _finish(resolutions: list[ValidationResolution]) -> ValidationResolveResult:
        _persist_trajectory()
        return ValidationResolveResult(resolutions, trajectory, artifacts)

    try:
        reset_command = f"git checkout --force {head_commit} && git clean -fd --quiet"
        started = time.time()
        reset_result = session.run_command(reset_command, timeout=120)
        trajectory.append(_trajectory_step(
            "setup",
            action="reset_to_head_commit",
            command=reset_command,
            returncode=reset_result.returncode,
            stdout=reset_result.stdout,
            stderr=reset_result.stderr,
            elapsed_seconds=time.time() - started,
        ))
        if reset_result.returncode != 0:
            error = f"git checkout failed: {reset_result.stderr[:500]}"
            return _finish([
                _make_resolution(
                    comment_index=i,
                    test=validation_tests[i],
                    initial_result=None,
                    final_result=None,
                    agent_diff="",
                    validation_test_diff="",
                    error=error,
                )
                for i in ordered_indices
            ])

        if any(validation_tests[i]["language"] == "python" for i in ordered_indices):
            install_command = "pip install -e . --no-deps --quiet"
            started = time.time()
            install_result = session.run_command(install_command, timeout=120)
            trajectory.append(_trajectory_step(
                "reinstall",
                stage="before_initial_validation",
                command=install_command,
                returncode=install_result.returncode,
                stdout=install_result.stdout,
                stderr=install_result.stderr,
                elapsed_seconds=time.time() - started,
            ))

        for i in ordered_indices:
            test = validation_tests[i]
            container_path = _copy_validation_test(
                session,
                test_code=test["test_code"],
                test_filename=test["test_filename"],
                source_test_path=test.get("source_test_path"),
            )
            trajectory.append(_trajectory_step(
                "copy_validation_tests",
                comment_index=i,
                source_test_path=str(test.get("source_test_path") or ""),
                container_test_path=container_path,
                generated_by_agent=bool(test.get("generated_by_agent")),
            ))
            test_comment = dict(test["comment"])
            test_comment["comment_index"] = i
            comments_for_prompt.append(test_comment)

        for i in ordered_indices:
            test = validation_tests[i]
            if test.get("generated_by_agent") and not test.get("test_code"):
                initial = {
                    "passed": False,
                    "output": (
                        "No existing generated validation test was available. "
                        "The agent must create this test file before fixing the code."
                    ),
                    "command": None,
                    "returncode": None,
                    "container_test_path": f"/workspace/{test['test_filename']}",
                    "elapsed_seconds": 0.0,
                }
            else:
                initial = _run_existing_validation_test(
                    session,
                    test_filename=test["test_filename"],
                    language=test["language"],
                )
            initial_results[i] = initial
            trajectory.append(_trajectory_step(
                "initial_validation",
                comment_index=i,
                test_file=test["test_filename"],
                language=test["language"],
                **initial,
            ))

        prompt = build_validation_prompt(
            comments=comments_for_prompt,
            validation_tests=validation_tests,
            initial_results=initial_results,
            patch_to_review=patch_to_review,
            repo=repo,
        )
        prompt_path = _write_artifact(artifact_dir, "prompt.txt", prompt, artifacts)
        trajectory.append(_trajectory_step(
            "agent_prompt",
            prompt=prompt,
            artifact_path=prompt_path,
            num_comments=len(ordered_indices),
        ))

        logger.info("  Invoking Qwen Code for %d validation test(s)...", len(ordered_indices))
        started = time.time()
        agent_stdout, agent_stderr, agent_rc = invoke_qwen_in_container(
            session,
            prompt,
            model,
            auth_type=qwen_auth_type,
            on_stream_event=_record_agent_stream_event,
        )
        stdout_path = _write_artifact(
            artifact_dir, "qwen_stdout.txt", agent_stdout, artifacts
        )
        stderr_path = _write_artifact(
            artifact_dir, "qwen_stderr.txt", agent_stderr, artifacts
        )
        trajectory.append(_trajectory_step(
            "agent_response",
            returncode=agent_rc,
            stdout=agent_stdout,
            stderr=agent_stderr,
            stdout_artifact_path=stdout_path,
            stderr_artifact_path=stderr_path,
            elapsed_seconds=time.time() - started,
        ))
        _persist_trajectory()

        diff_result = session.run_command("git diff", timeout=30)
        agent_diff = diff_result.stdout
        diff_path = _write_artifact(artifact_dir, "agent.diff", agent_diff, artifacts)
        trajectory.append(_trajectory_step(
            "post_agent_diff",
            command="git diff",
            returncode=diff_result.returncode,
            diff=agent_diff,
            artifact_path=diff_path,
            diff_chars=len(agent_diff),
        ))

        validation_test_diff = _capture_validation_test_diff(
            session,
            [validation_tests[i]["test_filename"] for i in ordered_indices],
        )
        validation_diff_path = _write_artifact(
            artifact_dir,
            "validation_tests.diff",
            validation_test_diff,
            artifacts,
        )
        trajectory.append(_trajectory_step(
            "validation_test_diff",
            diff=validation_test_diff,
            artifact_path=validation_diff_path,
            diff_chars=len(validation_test_diff),
        ))

        if any(validation_tests[i]["language"] == "python" for i in ordered_indices):
            install_command = "pip install -e . --no-deps --quiet"
            started = time.time()
            install_result = session.run_command(install_command, timeout=120)
            trajectory.append(_trajectory_step(
                "reinstall",
                stage="after_agent",
                command=install_command,
                returncode=install_result.returncode,
                stdout=install_result.stdout,
                stderr=install_result.stderr,
                elapsed_seconds=time.time() - started,
            ))

        for i in ordered_indices:
            test = validation_tests[i]
            final = _run_existing_validation_test(
                session,
                test_filename=test["test_filename"],
                language=test["language"],
            )
            final_results[i] = final
            trajectory.append(_trajectory_step(
                "final_validation",
                comment_index=i,
                test_file=test["test_filename"],
                language=test["language"],
                **final,
            ))

        resolutions = [
            _make_resolution(
                comment_index=i,
                test=validation_tests[i],
                initial_result=initial_results.get(i),
                final_result=final_results.get(i),
                agent_diff=agent_diff,
                validation_test_diff=validation_test_diff,
                error=None,
            )
            for i in ordered_indices
        ]
        return _finish(resolutions)

    except Exception as exc:
        logger.exception("  Error resolving instance with validation tests")
        trajectory.append(_trajectory_step("error", error=str(exc)))
        return _finish([
            _make_resolution(
                comment_index=i,
                test=validation_tests[i],
                initial_result=initial_results.get(i),
                final_result=final_results.get(i),
                agent_diff=agent_diff,
                validation_test_diff=validation_test_diff,
                error=str(exc),
            )
            for i in ordered_indices
        ])
