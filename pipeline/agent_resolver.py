"""Agent resolution of code review comments using Qwen Code inside Docker.

Builds prompts from review comments, invokes Qwen Code CLI inside a Docker
container, and verifies the agent's changes against Stage 3 tests.

All matched comments for an instance are batched into a single Qwen Code
invocation so the agent sees the full review context and makes one coherent
set of changes.
"""

from __future__ import annotations

import json
import logging
import shutil
import shlex
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

from execution.container_runtime import DockerContainerSession

logger = logging.getLogger(__name__)

# Qwen Code invocation timeout (seconds). Must be generous because the agent
# may read many files and make multiple edits in a large repo.
QWEN_TIMEOUT = 1200


def load_qwen_settings(settings_path: Path) -> dict:
    """Load the user's Qwen settings file, tolerating JSONC-style comments."""
    lines = []
    for line in settings_path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("//"):
            continue
        comment_pos = line.find(" //")
        if comment_pos != -1:
            line = line[:comment_pos]
        lines.append(line)
    return json.loads("\n".join(lines))


def get_qwen_auth_config(settings_path: Path) -> tuple[str | None, dict[str, str]]:
    """Extract auth type and env vars from the Qwen settings file."""
    if not settings_path.exists():
        return None, {}

    try:
        settings = load_qwen_settings(settings_path)
    except Exception as exc:
        logger.warning("Failed to parse Qwen settings from %s: %s", settings_path, exc)
        return None, {}

    auth_type = settings.get("security", {}).get("auth", {}).get("selectedType")
    if not isinstance(auth_type, str) or not auth_type:
        auth_type = None

    raw_env = settings.get("env", {})
    env = {
        str(key): str(value)
        for key, value in raw_env.items()
        if isinstance(key, str) and value is not None
    }
    return auth_type, env


def get_qwen_mounts(settings_path: Path) -> list[str]:
    """Build Docker volume mounts for host-installed Qwen Code."""
    qwen_path = shutil.which("qwen")
    node_path = shutil.which("node")
    if not qwen_path:
        raise RuntimeError("Host qwen binary was not found in PATH.")
    if not node_path:
        raise RuntimeError("Host node binary was not found in PATH.")

    qwen_cli = Path(qwen_path).resolve()
    qwen_package_dir = qwen_cli.parent
    node_binary = Path(node_path).resolve()

    if not qwen_cli.exists():
        raise RuntimeError(f"Resolved qwen CLI does not exist: {qwen_cli}")
    if not node_binary.exists():
        raise RuntimeError(f"Resolved node binary does not exist: {node_binary}")

    volumes = [
        f"{node_binary}:/opt/crab-node:ro",
        f"{qwen_package_dir}:/opt/crab-qwen-package:ro",
    ]
    if settings_path.exists():
        volumes.append(f"{settings_path}:/etc/qwen-settings.json:ro")
        volumes.append(f"{settings_path.parent}:/etc/qwen-home:ro")
    return volumes


@dataclass
class AgentResolution:
    """Result of attempting to resolve a single review comment with Qwen Code."""

    comment_index: int
    comment_text: str
    file_path: str
    resolved: bool          # Stage 3 test passed on agent's change
    test_passed: bool
    test_output: str
    agent_diff: str         # git diff of agent's changes (shared across batch)
    error: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentResolveResult:
    """Batch result plus the persisted execution trajectory."""

    resolutions: list[AgentResolution]
    trajectory: list[dict]
    artifacts: dict[str, str]


def _trajectory_step(phase: str, **details: object) -> dict:
    """Create a JSON-serializable trajectory event."""
    return {
        "phase": phase,
        "timestamp": time.time(),
        **details,
    }


def _write_artifact(
    artifact_dir: Path | None,
    filename: str,
    content: str,
    artifacts: dict[str, str],
) -> str | None:
    """Persist a large trajectory artifact and return its path."""
    if artifact_dir is None:
        return None
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / filename
    path.write_text(content or "", encoding="utf-8")
    artifacts[filename] = str(path)
    return str(path)


def _try_parse_json(text: str):
    """Parse Qwen JSON stdout when possible, otherwise keep the raw string."""
    try:
        return json.loads(text)
    except Exception:
        return text


def _extract_agent_stdout(raw_events: list[dict]) -> str:
    """Return the raw stdout captured from the Qwen invocation."""
    for event in reversed(raw_events):
        if event.get("phase") == "agent_response":
            return str(event.get("stdout") or "")
    return ""


def _extract_agent_stream_events(raw_events: list[dict]) -> list[dict]:
    """Return structured Qwen stream events captured during the invocation."""
    return [
        event["event"]
        for event in raw_events
        if event.get("phase") == "agent_stream_event"
        and isinstance(event.get("event"), dict)
    ]


def _serialize_stream_events(stream_events: list[dict]) -> str:
    """Serialize streamed Qwen events as JSONL, matching Qwen's stdout shape."""
    return "\n".join(
        json.dumps(event, ensure_ascii=False, default=str)
        for event in stream_events
    )


def _extract_comment_indices(raw_events: list[dict]) -> list[int]:
    """Best-effort fallback for older callers that do not pass comment indices."""
    indices = {
        event["comment_index"]
        for event in raw_events
        if isinstance(event.get("comment_index"), int)
    }
    return sorted(indices)


def write_agent_trajectory(
    *,
    artifact_dir: Path | None,
    instance: dict,
    model: str,
    agent: str,
    raw_events: list[dict],
    artifacts: dict[str, str],
    comment_indices: list[int] | None = None,
) -> str | None:
    """Write sample-compatible trajectory.json with raw and parsed Qwen stdout."""
    if artifact_dir is None:
        return None

    stream_events = _extract_agent_stream_events(raw_events)
    agent_stdout = (
        _serialize_stream_events(stream_events)
        if stream_events
        else _extract_agent_stdout(raw_events)
    )
    agent_stdout_parsed = stream_events if stream_events else _try_parse_json(agent_stdout)
    indices = comment_indices if comment_indices is not None else _extract_comment_indices(raw_events)
    trajectory = {
        "instance_id": instance["instance_id"],
        "agent": agent,
        "model": model,
        "turns": [
            {
                "comment_index": comment_index,
                "agent_stdout_raw": agent_stdout,
                "agent_stdout_parsed": agent_stdout_parsed,
            }
            for comment_index in indices
        ],
    }
    return _write_artifact(
        artifact_dir,
        "trajectory.json",
        json.dumps(trajectory, indent=2, ensure_ascii=False, default=str),
        artifacts,
    )


# Keep the old name as an alias so callers that were updated by a prior session
# do not break until they are updated below.
write_agent_stdout_trajectory = write_agent_trajectory


def build_test_command(container_test_path: str, language: str) -> str | None:
    """Build the in-container command for running one generated test."""
    if language == "python":
        return (
            f"python -m pytest {container_test_path} -x -v --tb=short --no-header "
            f"-c /dev/null -p no:cacheprovider"
        )
    if language in ("javascript", "typescript"):
        return f"npx jest --no-coverage {container_test_path}"
    if language == "go":
        test_dir = str(Path(container_test_path).parent)
        return f"go test -v -run . {test_dir}"
    return None


def build_tool_prompt(
    findings: list[dict],
    patch_to_review: str,
    repo: str,
) -> str:
    """Build prompt from tool-generated findings (file, issue_header, issue_content, start_line, end_line).

    Each finding becomes a section with file path, line range, issue header, and content.
    Includes the full PR diff as context.
    """
    sections = []
    for i, finding in enumerate(findings, 1):
        # Support both pr-agent (start_line/end_line) and devin (line) formats
        start_line = finding.get("start_line", "")
        end_line = finding.get("end_line", "")
        single_line = finding.get("line")
        if start_line and end_line:
            line_range = f" (lines {start_line}–{end_line})"
        elif single_line:
            line_range = f" (line {single_line})"
        else:
            line_range = ""

        # Support both pr-agent (issue_header/issue_content) and devin (type/description)
        header = finding.get("issue_header") or finding.get("type") or "Code Issue"
        content = finding.get("issue_content") or finding.get("description") or finding.get("comment") or ""

        sections.append(
            f"### Finding {i}\n"
            f"**File:** `{finding['file']}`{line_range}\n\n"
            f"**Issue:** {header}\n\n"
            f"{content}"
        )

    findings_block = "\n\n---\n\n".join(sections)

    return f"""You are resolving automated code review findings on the repository `{repo}`.

## Review Findings

{findings_block}

## Full PR Diff
```
{patch_to_review}
```

## Instructions
1. Read each finding and understand what code problem it identifies.
2. Modify the code to address ALL of the findings.
3. Make the minimal changes necessary — do not make unrelated modifications.
"""


def build_batch_prompt(
    comments: list[dict],
    patch_to_review: str,
    repo: str,
) -> str:
    """Build a single prompt covering all review comments for an instance.

    Each comment includes its text, file path, and diff hunk.
    Excludes: test code, merged_patch, after-file content.
    """
    sections = []
    for i, comment in enumerate(comments, 1):
        sections.append(
            f"### Comment {i}\n"
            f"**File:** `{comment['path']}`\n\n"
            f"**Diff hunk being reviewed:**\n"
            f"```\n{comment.get('diff_hunk', '')}\n```\n\n"
            f"**Reviewer says:**\n{comment['text']}"
        )

    comments_block = "\n\n---\n\n".join(sections)

    return f"""You are resolving code review comments on the repository `{repo}`.

## Review Comments

{comments_block}

## Instructions
1. Read each review comment and understand what change the reviewer is requesting.
2. Modify the code to address ALL of the reviewer's feedback.
3. Make the minimal changes necessary — do not make unrelated modifications.
"""


def setup_qwen_in_container(session: DockerContainerSession) -> None:
    """Expose host-installed Qwen Code inside the container."""
    check = session.run_command(
        "test -x /opt/crab-node && test -f /opt/crab-qwen-package/cli.js",
        timeout=10,
    )
    if check.returncode != 0:
        raise RuntimeError(
            "Qwen host mounts not found. Expected /opt/crab-node and "
            "/opt/crab-qwen-package/cli.js inside the container."
        )

    session.run_command(
        (
            "printf '#!/bin/sh\\nexec /opt/crab-node /opt/crab-qwen-package/cli.js \"$@\"\\n'"
            " > /usr/local/bin/qwen && chmod +x /usr/local/bin/qwen"
        ),
        timeout=10,
    )
    logger.info("Qwen Code wrapper installed from host-mounted runtime")

    session.run_command(
        "mkdir -p /root/.qwen && "
        "cp -a /etc/qwen-home/. /root/.qwen/ 2>/dev/null || true; "
        "cp /etc/qwen-settings.json /root/.qwen/settings.json 2>/dev/null || true",
        timeout=10,
    )

    result = session.run_command("git config --global --add safe.directory /workspace", timeout=30)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to configure git safe.directory: {result.stderr[-1000:]}"
        )


def invoke_qwen_in_container(
    session: DockerContainerSession,
    prompt: str,
    model: str,
    auth_type: str | None = None,
    on_stream_event: Callable[[dict], None] | None = None,
) -> tuple[str, str, int]:
    """Run host-mounted Qwen Code in headless mode as root.

    The prompt is written to /tmp/prompt.txt inside the container and then
    piped to qwen's stdin via ``-p -``.  This avoids passing the (potentially
    very large) prompt as a command-line argument, which would hit the kernel's
    ARG_MAX limit on instances with large PR diffs.

    Returns (stdout, stderr, returncode).
    """
    prompt_path = "/tmp/prompt.txt"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_prompt.txt", delete=False
    ) as f:
        f.write(prompt)
        local_prompt = Path(f.name)
    try:
        session.copy_to(local_prompt, prompt_path)
    finally:
        local_prompt.unlink(missing_ok=True)

    # Build extra flags (no -p value here — prompt is fed via stdin below).
    extra_flags = ["--yolo", "--output-format", "stream-json"]
    if auth_type:
        extra_flags.extend(["--auth-type", shlex.quote(auth_type)])
    if model:
        extra_flags.extend(["--model", shlex.quote(model)])
    extra_str = " ".join(extra_flags)

    # Feed the prompt file to qwen's stdin with `-p -`.
    # This bypasses execve's ARG_MAX limit entirely — the prompt never appears
    # in any argv; the kernel only sees a short command string.
    shell_cmd = (
        "export QWEN_TELEMETRY=false && "
        f"cd /workspace && "
        f"qwen -p - {extra_str} < {shlex.quote(prompt_path)}"
    )
    cmd = ["bash", "-lc", shell_cmd]

    def handle_stdout_line(line: str) -> None:
        if on_stream_event is None:
            return
        line = line.strip()
        if not line:
            return
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            event = {"type": "raw", "text": line}
        on_stream_event(event)

    logger.info("  Invoking qwen (prompt_bytes=%d, flags=%s)", len(prompt.encode()), extra_str)
    result = session.run_command_stream(
        cmd,
        timeout=QWEN_TIMEOUT,
        on_stdout_line=handle_stdout_line,
    )
    if result.returncode != 0:
        logger.warning("  Qwen stderr: %s", (result.stderr or "")[:500])
    return result.stdout, result.stderr, result.returncode


def verify_with_test(
    session: DockerContainerSession,
    test_code: str,
    test_filename: str,
    language: str,
) -> tuple[bool, str]:
    """Write test into container and run it. Returns (passed, output).

    Uses -c /dev/null -p no:cacheprovider for isolation (Python).
    """
    # Write test code to a temp file and copy into container
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

    run_cmd = build_test_command(container_test_path, language)
    if run_cmd is None:
        return False, f"Execution not supported for language: {language}"

    result = session.run_command(run_cmd, timeout=120)
    combined = (result.stdout + "\n" + result.stderr).strip()
    passed = result.returncode == 0
    return passed, combined


def verify_with_test_details(
    session: DockerContainerSession,
    test_code: str,
    test_filename: str,
    language: str,
) -> dict:
    """Write and run one test, returning execution details for trajectories."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f"_{test_filename}", delete=False
    ) as f:
        f.write(test_code)
        local_test_path = Path(f.name)

    container_test_path = f"/workspace/{test_filename}"
    try:
        session.copy_to(local_test_path, container_test_path)
    finally:
        local_test_path.unlink(missing_ok=True)

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
    elapsed = time.time() - started
    combined = (result.stdout + "\n" + result.stderr).strip()
    return {
        "passed": result.returncode == 0,
        "output": combined,
        "command": run_cmd,
        "returncode": result.returncode,
        "container_test_path": container_test_path,
        "elapsed_seconds": elapsed,
    }


def resolve_instance(
    instance: dict,
    matched_comments: dict[int, tuple[dict, str, str]],
    session: DockerContainerSession,
    model: str,
    language: str,
    qwen_auth_type: str | None = None,
    artifact_dir: Path | None = None,
) -> AgentResolveResult:
    """Resolve all matched comments for an instance in a single Qwen invocation.

    Args:
        instance: The dataset instance dict.
        matched_comments: Mapping of comment_index -> (comment_dict, test_code, test_filename).
        session: Active Docker container session.
        model: Qwen model to use. If empty, Qwen uses its configured default.
        language: Programming language for test execution.

    Flow:
        1. Reset to head_commit, reinstall
        2. Build a single prompt with all comments
        3. Invoke Qwen Code once
        4. Capture git diff
        5. Reinstall (agent may have edited source)
        6. Verify each Stage 3 test individually
        7. Return resolutions plus the exported agent trajectory
    """
    head_commit = instance["commit_to_review"]["head_commit"]
    repo = instance["repo"]
    patch_to_review = instance["commit_to_review"]["patch_to_review"]

    # Collect comments in index order for prompt building
    ordered_indices = sorted(matched_comments.keys())
    comments_for_prompt = [matched_comments[i][0] for i in ordered_indices]
    trajectory: list[dict] = []
    artifacts: dict[str, str] = {}

    def _persist_trajectory() -> None:
        write_agent_trajectory(
            artifact_dir=artifact_dir,
            instance=instance,
            model=model,
            agent="qwen-code",
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
        # 1. Reset to head commit
        reset_command = f"git checkout --force {head_commit} && git clean -fd --quiet"
        started = time.time()
        reset_result = session.run_command(
            reset_command,
            timeout=120,
        )
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
                    resolved=False, test_passed=False, test_output="",
                    agent_diff="", error=error,
                )
                for i in ordered_indices
            ])

        # 2. Reinstall
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

        # 3. Build batch prompt and invoke Qwen Code once
        prompt = build_batch_prompt(
            comments=comments_for_prompt,
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
        logger.info("  Invoking Qwen Code for %d comment(s)...", len(ordered_indices))
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
        logger.info("  Qwen Code returned (rc=%d, output=%d chars)", agent_rc, len(agent_stdout))

        # 4. Capture git diff
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
                    resolved=False, test_passed=False, test_output="",
                    agent_diff="", error="Agent made no changes",
                )
                for i in ordered_indices
            ])

        # 5. Reinstall (agent may have edited source)
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

        # 6. Verify each Stage 3 test individually
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
                "  Comment %d test result: %s", i, "PASS" if test_passed else "FAIL"
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

    except Exception as e:
        logger.exception("  Error resolving instance")
        trajectory.append(_trajectory_step(
            "error",
            error=str(e),
        ))
        return _finish([
            AgentResolution(
                comment_index=i,
                comment_text=matched_comments[i][0]["text"],
                file_path=matched_comments[i][0]["path"],
                resolved=False, test_passed=False, test_output="",
                agent_diff="", error=str(e),
            )
            for i in ordered_indices
        ])
