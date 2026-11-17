"""Intent-guided Qwen resolver for code review comments.

This variant keeps the baseline resolver lifecycle and prompt shape but
augments each review comment with a precomputed edit intent and the
classifier's why / concern / expectation analysis.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline.agent_resolver import (
    AgentResolution,
    AgentResolveResult,
    _trajectory_step,
    _write_artifact,
    invoke_qwen_in_container,
    verify_with_test_details,
    write_agent_trajectory,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "qwen-code-with-intent"
DEFAULT_INTENT_FILE = "task_classification/comment_task_qwen.jsonl"

LABEL_TO_TASK_TYPE: dict[str, str] = {
    "bugfix": "bugfixing",
    "bugfixing": "bugfixing",
    "documentation": "documentation",
    "logging": "other",
    "other": "other",
    "others": "other",
    "refactoring": "refactoring",
}

INTENT_DETAIL_FIELDS = ("why", "concern", "expectation")

# (instance_id, comment_index) -> {"why": ..., "concern": ..., "expectation": ...}
# populated alongside load_precomputed_intents(); kept separate so the
# task-type lookup consumed by the runner scripts stays a plain str mapping
_intent_details: dict[tuple[str, int], dict[str, str]] = {}


def normalize_intent_label(label: object) -> str:
    """Normalize a dataset intent label to one of the registered task types."""
    if not isinstance(label, str):
        return "other"
    return LABEL_TO_TASK_TYPE.get(label.strip().lower(), "other")


def load_precomputed_intents(jsonl_path: str | Path) -> dict[tuple[str, int], str]:
    """Load ``(instance_id, comment_index) -> task_type`` from intent JSONL."""
    path = Path(jsonl_path)
    lookup: dict[tuple[str, int], str] = {}
    if not path.exists():
        logger.warning("Precomputed intent file not found: %s", path)
        return lookup

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                instance_id = str(record["instance_id"])
                comment_index = int(record["comment_index"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                logger.warning(
                    "Skipping malformed intent row %s:%d: %s",
                    path,
                    line_number,
                    exc,
                )
                continue
            lookup[(instance_id, comment_index)] = normalize_intent_label(
                record.get("label")
            )
            details = {
                field: str(record.get(field) or "")
                for field in INTENT_DETAIL_FIELDS
            }
            # older intent files carry a single "reasoning" field instead
            if not details["why"] and record.get("reasoning"):
                details["why"] = str(record["reasoning"])
            _intent_details[(instance_id, comment_index)] = details
    return lookup


def get_intent_details(instance_id: str, comment_index: int) -> dict[str, str]:
    """Return the why/concern/expectation details for one classified comment."""
    return _intent_details.get((instance_id, comment_index), {})


def _intent_map_for_instance(
    *,
    instance_id: str,
    ordered_indices: list[int],
    intent_lookup: dict[tuple[str, int], str] | None,
) -> dict[int, str]:
    intent_map: dict[int, str] = {}
    lookup = intent_lookup or {}
    for index in ordered_indices:
        intent_map[index] = lookup.get((instance_id, index), "other")
    return intent_map


def build_batch_prompt_with_intent(
    comments: list[dict],
    repo: str,
    *,
    intent_by_comment_index: dict[int, str],
    intent_details_by_comment_index: dict[int, dict[str, str]] | None = None,
) -> str:
    """Build a baseline-style batch prompt enriched with per-comment edit intent."""
    details_by_index = intent_details_by_comment_index or {}
    sections = []
    for ordinal, comment in enumerate(comments, start=1):
        comment_index = int(comment["comment_index"])
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
        sections.append(
            f"### Comment {ordinal}\n"
            f"**File:** `{comment['path']}`\n\n"
            f"**Diff hunk being reviewed:**\n"
            f"```\n{comment.get('diff_hunk', '')}\n```\n\n"
            f"**Reviewer says:**\n{comment['text']}\n\n"
            f"**Edit intent:** `{task_type}`\n\n"
            f"{detail_lines}".rstrip()
        )

    comments_block = "\n\n---\n\n".join(sections)

    return f"""You are resolving code review comments on the repository `{repo}`.

## Review Comments

{comments_block}

## Instructions
1. Read each review comment and understand what change the reviewer is requesting.
   Each comment has a pre-classified edit intent and, when available, an analysis
   of why the reviewer commented, their concern, and their expectation — use these
   as guidance for the edit.
2. Modify the code to address ALL of the reviewer's feedback.
3. Make the minimal changes necessary — do not make unrelated modifications.
"""


def resolve_instance_with_intent(
    instance: dict,
    matched_comments: dict[int, tuple[dict, str, str]],
    session: DockerContainerSession,
    model: str,
    language: str,
    qwen_auth_type: str | None = None,
    artifact_dir: Path | None = None,
    intent_lookup: dict[tuple[str, int], str] | None = None,
) -> AgentResolveResult:
    """Resolve matched comments with precomputed intent guidance."""
    head_commit = instance["commit_to_review"]["head_commit"]
    repo = instance["repo"]
    instance_id = str(instance.get("instance_id", ""))
    ordered_indices = sorted(matched_comments.keys())
    comments_for_prompt = []
    for index in ordered_indices:
        comment_for_prompt = dict(matched_comments[index][0])
        comment_for_prompt["comment_index"] = index
        comments_for_prompt.append(comment_for_prompt)

    intent_by_index = _intent_map_for_instance(
        instance_id=instance_id,
        ordered_indices=ordered_indices,
        intent_lookup=intent_lookup,
    )
    intent_details_by_index = {
        index: get_intent_details(instance_id, index) for index in ordered_indices
    }
    trajectory: list[dict] = []
    artifacts: dict[str, str] = {}

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

    def _finish(resolutions: list[AgentResolution]) -> AgentResolveResult:
        _persist_trajectory()
        return AgentResolveResult(resolutions, trajectory, artifacts)

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
                AgentResolution(
                    comment_index=i,
                    comment_text=matched_comments[i][0]["text"],
                    file_path=matched_comments[i][0]["path"],
                    resolved=False,
                    test_passed=False,
                    test_output="",
                    agent_diff="",
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

        if language == "python":
            install_command = "pip install -e . --no-deps --quiet"
            started = time.time()
            install_result = session.run_command(install_command, timeout=120)
            trajectory.append(_trajectory_step(
                "reinstall",
                stage="before_agent",
                command=install_command,
                returncode=install_result.returncode,
                stdout=install_result.stdout,
                stderr=install_result.stderr,
                elapsed_seconds=time.time() - started,
            ))

        prompt = build_batch_prompt_with_intent(
            comments=comments_for_prompt,
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
            "  Invoking Qwen Code with intent for %d comment(s)...",
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
        logger.info(
            "  Qwen Code with intent returned (rc=%d, output=%d chars)",
            agent_rc,
            len(agent_stdout),
        )

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

        no_changes = False
        if not agent_diff.strip():
            status_result = session.run_command("git status --porcelain", timeout=15)
            if not status_result.stdout.strip():
                no_changes = True

        if no_changes:
            return _finish([
                AgentResolution(
                    comment_index=i,
                    comment_text=matched_comments[i][0]["text"],
                    file_path=matched_comments[i][0]["path"],
                    resolved=False,
                    test_passed=False,
                    test_output="",
                    agent_diff="",
                    error="Agent made no changes",
                )
                for i in ordered_indices
            ])

        if language == "python":
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

        resolutions = []
        for i in ordered_indices:
            comment, test_code, test_filename = matched_comments[i]
            test_details = verify_with_test_details(
                session, test_code, test_filename, language
            )
            test_passed = bool(test_details["passed"])
            test_output = str(test_details["output"])
            trajectory.append(_trajectory_step(
                "stage3_test_verification",
                comment_index=i,
                test_file=test_filename,
                language=language,
                **test_details,
            ))
            logger.info(
                "  Comment %d intent test result: %s",
                i,
                "PASS" if test_passed else "FAIL",
            )
            resolutions.append(AgentResolution(
                comment_index=i,
                comment_text=comment["text"],
                file_path=comment["path"],
                resolved=test_passed,
                test_passed=test_passed,
                test_output=test_output,
                agent_diff=agent_diff,
                error=None,
            ))
        return _finish(resolutions)

    except Exception as exc:
        logger.exception("  Error resolving instance with intent")
        trajectory.append(_trajectory_step("error", error=str(exc)))
        return _finish([
            AgentResolution(
                comment_index=i,
                comment_text=matched_comments[i][0]["text"],
                file_path=matched_comments[i][0]["path"],
                resolved=False,
                test_passed=False,
                test_output="",
                agent_diff="",
                error=str(exc),
            )
            for i in ordered_indices
        ])
