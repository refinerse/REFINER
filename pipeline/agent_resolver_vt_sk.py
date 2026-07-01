"""Validation-test and intent guided Qwen resolver.

This variant keeps the validation-test repair lifecycle (copy generated tests
into the container, run them before and after the agent, capture the test diff)
and augments each review comment with a pre-classified edit intent and the
classifier's why / concern / expectation analysis, embedded directly in the prompt.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline.agent_resolver import (
    _trajectory_step,
    _write_artifact,
    invoke_qwen_in_container,
    write_agent_trajectory,
)
from pipeline.agent_resolver_validation_test import (
    ValidationResolution,
    ValidationResolveResult,
    _capture_validation_test_diff,
    _copy_validation_test,
    _make_resolution,
    _run_existing_validation_test,
)
from pipeline.agent_resolver_with_task import (
    _intent_map_for_instance,
    get_intent_details,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "qwen-code-validation-test-with-intent"


def _make_naive_resolution(
    *,
    comment_index: int,
    test: dict,
    agent_diff: str,
    error: str | None,
) -> ValidationResolution:
    """Build a resolution for a comment with no validation test.

    These comments are resolved by edit-intent guidance only (no validation
    signal), mirroring the ``with_intent`` resolver. The validation-specific
    fields are left neutral; correctness is judged by the separate groundtruth
    assessment in the runner.
    """
    comment = test["comment"]
    return ValidationResolution(
        comment_index=comment_index,
        comment_text=comment.get("text", ""),
        file_path=comment.get("path", ""),
        language=test.get("language", "python"),
        validation_test_file="",
        validation_initial_passed=False,
        validation_initial_output="(no validation test — naive intent resolution)",
        validation_final_passed=False,
        validation_final_output="",
        expected_failure_observed=False,
        initial_unexpected_pass=False,
        validation_test_revised=False,
        resolved=False,
        agent_diff=agent_diff,
        validation_test_diff="",
        error=error,
    )


def build_validation_intent_prompt(
    *,
    comments: list[dict],
    validation_tests: dict[int, dict],
    initial_results: dict[int, dict],
    repo: str,
    intent_by_comment_index: dict[int, str],
    intent_details_by_comment_index: dict[int, dict[str, str]] | None = None,
) -> str:
    """Build the combined validation-test and edit-intent repair prompt."""
    details_by_index = intent_details_by_comment_index or {}
    sections = []
    for ordinal, comment in enumerate(comments, 1):
        comment_index = int(comment["comment_index"])
        test = validation_tests[comment_index]
        task_type = intent_by_comment_index.get(comment_index, "other")
        details = details_by_index.get(comment_index, {})
        detail_lines = "".join(
            f"**{title}:** {details[field]}\n\n"
            for field, title in (
                ("why", "Why the reviewer commented"),
                ("concern", "Reviewer's concern"),
                ("expectation", "Reviewer's expectation"),
            )
            if details.get(field)
        )
        header = (
            f"### Comment {ordinal} (dataset index {comment_index})\n"
            f"**File:** `{comment['path']}`\n\n"
            f"**Diff hunk being reviewed:**\n"
            f"```\n{comment.get('diff_hunk', '')}\n```\n\n"
            f"**Reviewer says:**\n{comment['text']}\n\n"
        )
        if test.get("no_validation_test"):
            # Intent-only fallback: no validation test exists for this comment.
            sections.append(
                (
                    header
                    + "**No validation test is available for this comment.** Resolve it "
                    "directly from the reviewer feedback and the edit intent below; "
                    "do not create a validation test for it.\n\n"
                    f"**Edit intent:** `{task_type}`\n\n"
                    f"{detail_lines}"
                ).rstrip()
            )
            continue
        initial = initial_results[comment_index]
        initial_status = "PASSED" if initial["passed"] else "FAILED"
        validation_note = (
            "This validation test file did not exist before the agent run. "
            "Create it at the named path, make it fail on the current "
            "unaddressed issue, then fix the production code so it passes."
            if test.get("generated_by_agent")
            else "This validation test was generated before the agent run."
        )
        sections.append(
            (
                header
                + f"**Validation test:** `/workspace/{test['test_filename']}`\n\n"
                f"**Validation test note:** {validation_note}\n\n"
                f"**Initial validation result on current code:** {initial_status}\n"
                f"**Command:** `{initial.get('command')}`\n"
                f"**Output:**\n```\n{initial.get('output', '')}\n```\n\n"
                f"**Edit intent:** `{task_type}`\n\n"
                f"{detail_lines}"
            ).rstrip()
        )

    comments_block = "\n\n---\n\n".join(sections)

    return f"""You are an experienced software engineer resolving code review comments on the
repository `{repo}`. Work like a careful contributor preparing a focused
follow-up commit: address exactly what the reviewers asked for, and nothing else.

## How to use the validation tests
Validation tests have been copied into `/workspace` (e.g.
`/workspace/test_review_comment_N.py`). They are a *repair-time signal only* —
an aid for checking your fix, NOT proof of ground-truth correctness. Each comment
section below names the exact test file for that comment. Inspect and run those
named files as you work; do not rely on them as the final word.

Resolving a comment means the production code is correct — not that the
validation test is green. A passing validation test is necessary but not
sufficient; a change that only makes the test pass without addressing the
underlying concern is a failure.

Some comments have no validation test (they are marked accordingly below). For
those, resolve the production code directly from the reviewer feedback and the
edit intent — do not create a test for them; you simply won't have a test to
check them with.

## How to read each comment
Every comment below includes a pre-classified **Edit intent** and, when
available, an analysis of the reviewer's perspective:
- **Why the reviewer commented** — what triggered the comment.
- **Reviewer's concern** — the underlying problem they want avoided.
- **Reviewer's expectation** — the change they expect to see.
Treat this analysis as guidance for intent, not as literal edit instructions.
Comments are independent: do not assume they share an intent or touch the same
code.

## Review Comments And Validation Results

{comments_block}

## Procedure
1. For each comment, understand the requested change from the reviewer text,
   diff hunk, and the edit-intent analysis (why / concern / expectation).
2. Establish the validation signal before editing production code:
   - If the named validation test file is missing, create it at the
     `/workspace/...` path so it captures the reviewer's concern and FAILS on the
     current, unaddressed code.
   - If the test already exists, run it on the current code first.
   - If a test unexpectedly PASSED on the current code, it is not yet capturing
     the concern — revise it so it fails on the unaddressed issue before you fix
     the code.
3. Fix the production code to address ALL reviewer feedback, guided by the
   edit intent. The diff hunk shows ONE location, but reviewer comments often
   point at one instance of a problem that recurs elsewhere — search the
   surrounding file/module for other occurrences of the same issue and fix every
   one of them, not just the location in the hunk.
4. Re-run the relevant validation tests as you work and iterate until they pass.
5. Before finishing, re-read each reviewer comment in full (including any
   follow-up discussion) and confirm every distinct point is addressed —
   reviewers sometimes call out additional locations or follow-up requirements.

## Engineering constraints
- Make the smallest change that fully resolves each comment. Do not refactor,
  reformat, rename, or "improve" code outside the scope of the feedback.
- Match the surrounding code's existing conventions, style, naming, and patterns.
- Preserve existing behavior and public APIs unless a comment explicitly asks to
  change them; do not break unrelated functionality or existing tests.
- You may repair a validation test's setup/fixtures so it runs correctly, but do
  NOT weaken or remove the assertion that encodes the reviewer's concern. If
  making the test pass would require changing that assertion, the production fix
  is wrong — fix the code instead.
- Address every comment — do not leave any reviewer feedback unresolved.
- Confine production edits to the files/areas implicated by the comments and
  their validation tests.
"""


def resolve_instance_vt_sk(
    *,
    instance: dict,
    validation_tests: dict[int, dict],
    session: DockerContainerSession,
    model: str,
    qwen_auth_type: str | None = None,
    artifact_dir: Path | None = None,
    intent_lookup: dict[tuple[str, int], str] | None = None,
) -> ValidationResolveResult:
    """Resolve comments with validation tests plus edit-intent guidance."""
    head_commit = instance["commit_to_review"]["head_commit"]
    repo = instance["repo"]
    instance_id = str(instance.get("instance_id", ""))
    ordered_indices = sorted(validation_tests.keys())
    comments_for_prompt = []
    trajectory: list[dict] = []
    artifacts: dict[str, str] = {}
    initial_results: dict[int, dict] = {}
    final_results: dict[int, dict] = {}
    agent_diff = ""
    validation_test_diff = ""
    intent_by_index = _intent_map_for_instance(
        instance_id=instance_id,
        ordered_indices=ordered_indices,
        intent_lookup=intent_lookup,
    )
    intent_details_by_index = {
        index: get_intent_details(instance_id, index) for index in ordered_indices
    }

    def _persist_trajectory() -> None:
        write_agent_trajectory(
            artifact_dir=artifact_dir,
            instance=instance,
            model=model,
            agent=AGENT_NAME,
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

        intent_map_payload = {
            str(index): {
                "task_type": intent_by_index[index],
                **intent_details_by_index.get(index, {}),
            }
            for index in ordered_indices
        }
        intent_path = _write_artifact(
            artifact_dir,
            "intent_map.json",
            json.dumps(intent_map_payload, indent=2, sort_keys=True),
            artifacts,
        )
        trajectory.append(_trajectory_step(
            "intent_mapping",
            intent_by_comment_index=intent_by_index,
            intent_details_by_comment_index=intent_details_by_index,
            artifact_path=intent_path,
        ))

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
            if not test.get("no_validation_test"):
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
            if test.get("no_validation_test"):
                continue
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

        prompt = build_validation_intent_prompt(
            comments=comments_for_prompt,
            validation_tests=validation_tests,
            initial_results=initial_results,
            repo=repo,
            intent_by_comment_index=intent_by_index,
            intent_details_by_comment_index=intent_details_by_index,
        )
        prompt_path = _write_artifact(artifact_dir, "prompt.txt", prompt, artifacts)
        trajectory.append(_trajectory_step(
            "agent_prompt",
            prompt=prompt,
            artifact_path=prompt_path,
            num_comments=len(ordered_indices),
            intent_by_comment_index=intent_by_index,
        ))

        logger.info(
            "  Invoking Qwen Code with validation tests and intent for %d comment(s)...",
            len(ordered_indices),
        )
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
            [
                validation_tests[i]["test_filename"]
                for i in ordered_indices
                if not validation_tests[i].get("no_validation_test")
            ],
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
            if test.get("no_validation_test"):
                continue
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
            _make_naive_resolution(
                comment_index=i,
                test=validation_tests[i],
                agent_diff=agent_diff,
                error=None,
            )
            if validation_tests[i].get("no_validation_test")
            else _make_resolution(
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
        logger.exception("  Error resolving instance with validation tests and intent")
        trajectory.append(_trajectory_step("error", error=str(exc)))
        return _finish([
            _make_naive_resolution(
                comment_index=i,
                test=validation_tests[i],
                agent_diff=agent_diff,
                error=str(exc),
            )
            if validation_tests[i].get("no_validation_test")
            else _make_resolution(
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
