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
from dataclasses import dataclass, field
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

# Each seed steers the generation agent toward a different inference strategy and
# is designed to prevent a specific failure pattern observed in prior runs.
DIVERSITY_SEEDS = [
    # Seed 0 — runtime behavior (prevents: AST/source-text tests that miss behavioral correctness)
    "Inference strategy: RUNTIME BEHAVIOR ONLY. "
    "Call the function or instantiate the class and observe actual outputs, return values, "
    "raised exceptions, or state changes. Do NOT read the source file as a string, do NOT use "
    "ast.parse, do NOT grep the file. If the reviewer's concern can only be observed at runtime, "
    "you must find a way to do so. If import truly fails, only then fall back to source inspection.",
    # Seed 1 — boundary/absence condition (prevents: happy-path tests that ignore the edge case)
    "Inference strategy: BOUNDARY OR ABSENCE CONDITION. "
    "Identify the specific input value, boundary, or absence condition the reviewer was worried about "
    "(e.g. None, empty string, zero, negative value, missing key, duplicate entry). "
    "Your test must use that exact boundary as input. "
    "If the reviewer said something should NOT happen or should be removed, assert its ABSENCE — "
    "do not just assert the positive case is present.",
    # Seed 2 — public API contract (prevents: internal-implementation tests that miss the API shape)
    "Inference strategy: PUBLIC API CONTRACT. "
    "Identify whether the reviewer discussed a specific function name, method signature, class "
    "attribute, module-level name, or public interface. If so, verify it at runtime via introspection "
    "(getattr, hasattr, inspect.signature) or by calling it directly — not by reading source text. "
    "If the reviewer's concern is purely behavioral (not naming/structure), verify that the EXACT "
    "invariant the reviewer described holds: e.g. consistent values, correct type conversion, "
    "no silent data loss, proper error propagation.",
]


@dataclass
class ContextReport:
    """Structured output from the Phase 1 exploration agent."""

    test_framework: str = "unknown"
    test_directory: str = "unknown"
    run_command: str = (
        "cd /workspace && python -m pytest {test_file} -x -v --tb=short"
        " --no-header -c /dev/null -p no:cacheprovider"
    )
    import_status: dict[str, str] = field(default_factory=dict)
    related_test_files: list[str] = field(default_factory=list)
    example_test: str = ""
    fixtures_available: str = "none"
    raw_output: str = ""


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


# ---------------------------------------------------------------------------
# Phase 1 — context exploration
# ---------------------------------------------------------------------------


def _build_exploration_prompt(comment_jobs: list[dict]) -> str:
    """Build a directive exploration prompt (structured like a skill file)."""
    file_list = "\n".join(
        f"- /workspace/{job['path']}"
        for job in {job["path"]: job for job in comment_jobs}.values()
    )
    # derive dotted module paths for Python files
    module_list = "\n".join(
        f"  python -c \"import {job['path'].replace('/', '.').replace('.py', '')}\" 2>&1"
        for job in {job["path"]: job for job in comment_jobs}.values()
        if job["language"] == "python"
    )
    grep_examples = "\n".join(
        "  grep -rl \"{mod_import}\" /workspace/tests/ /workspace/test/ 2>/dev/null | head -5".format(
            mod_import=(
                "from {mod} import\\|import {mod}".format(
                    mod=job["path"].replace("/", ".").replace(".py", "")
                )
            )
        )
        for job in {job["path"]: job for job in comment_jobs}.values()
        if job["language"] == "python"
    )
    return f"""You are Qwen Code inside /workspace. Your ONLY job is to explore and report.
Do NOT write any test files or modify any files.

## Target source files under review
{file_list}

## Mandatory exploration steps (run each in order)

### Step 1 — Detect test framework
Run these commands and record output:
  find /workspace -maxdepth 3 -name "pytest.ini" -o -name "setup.cfg" -o -name "pyproject.toml" -o -name "jest.config.*" -o -name "go.mod" | head -10
  cat /workspace/pytest.ini 2>/dev/null || grep -A5 "\\[tool.pytest" /workspace/pyproject.toml 2>/dev/null | head -10

### Step 2 — Find test directory
  find /workspace -maxdepth 3 -type d \\( -name "test" -o -name "tests" -o -name "test_*" \\) | head -5

### Step 3 — Find related test files for each target source file
Run each of the following and record paths returned:
{grep_examples if grep_examples else "  # (no Python files to grep for)"}

### Step 4 — Check importability for each Python target file
Run each and record "ok" or the first error line:
{module_list if module_list else "  # (no Python files to import-check)"}

### Step 5 — Read one related test file (shortest one found in Step 3)
Read the first 60 lines. Copy a representative 15-20 line test function verbatim.

### Step 6 — Check for conftest.py
  find /workspace -name "conftest.py" | head -3
If found, read the first 40 lines and note fixture names defined.

## Required output
After completing all steps, return EXACTLY this fenced block and nothing else:

```report
test_framework: <pytest|jest|go_test|unknown>
test_directory: <path or unknown>
run_command: cd /workspace && python -m pytest {{test_file}} -x -v --tb=short --no-header -c /dev/null -p no:cacheprovider
import_status:
  dotted.module.path: ok
related_test_files:
  - tests/test_foo.py
example_test: |
  def test_something():
      assert True
fixtures_available: <comma-separated names or none>
```
"""


def _extract_text_from_stream_json(raw: str) -> str:
    """Extract plain text output from Qwen streaming JSON format.

    The agent stdout is a series of JSON lines. The last ``result`` event
    contains the full text reply in its ``result`` field.  Fall back to the
    raw string if no such event is found (plain-text output path).
    """
    # Try to pull the `result` field from the last result event
    for line in reversed(raw.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            if event.get("type") == "result" and "result" in event:
                return str(event["result"])
        except (json.JSONDecodeError, ValueError):
            continue
    # No result event found — return the raw text as-is
    return raw


def _parse_context_report(agent_stdout: str) -> ContextReport:
    """Extract the ```report block from agent stdout and parse it into ContextReport.

    Falls back to an empty ContextReport if the block is missing or malformed —
    generation proceeds without pre-explored context rather than hard-failing.
    """
    text = _extract_text_from_stream_json(agent_stdout)
    match = re.search(r"```report\n(.*?)```", text, re.DOTALL)
    if not match:
        logger.warning("Exploration agent produced no parseable ```report block")
        return ContextReport(raw_output=text)

    raw_block = match.group(1)
    report = ContextReport(raw_output=text)
    try:
        current_key: str | None = None
        list_values: list[str] = []
        block_lines: list[str] = []
        in_block = False

        def _flush_pending() -> None:
            nonlocal list_values, current_key
            if not list_values:
                return
            if current_key == "import_status":
                for item in list_values:
                    item = item.lstrip("- ").strip()
                    if ": " in item:
                        k, _, v = item.partition(": ")
                        report.import_status[k.strip()] = v.strip()
            elif current_key == "related_test_files":
                report.related_test_files.extend(
                    item.lstrip("- ").strip() for item in list_values if item.strip()
                )
            list_values = []
            current_key = None

        for line in raw_block.splitlines():
            # Inside a YAML block scalar (|)
            if in_block:
                if line.startswith("  ") or line == "":
                    block_lines.append(line[2:] if line.startswith("  ") else "")
                    continue
                # End of block — flush it
                if current_key == "example_test":
                    report.example_test = "\n".join(block_lines).rstrip()
                in_block = False
                block_lines = []
                # fall through to parse this line normally

            # Indented list / mapping items (belong to the current_key section)
            if line.startswith("  ") and current_key in (
                "import_status",
                "related_test_files",
            ):
                list_values.append(line.strip())
                continue

            # Any non-indented line ends a pending list section
            if list_values:
                _flush_pending()

            stripped = line.rstrip()
            if not stripped:
                continue

            # Block scalar header: "key: |"
            if re.match(r"^(\w+):\s*\|$", stripped):
                _flush_pending()
                current_key = stripped.split(":")[0].strip()
                in_block = True
                block_lines = []
                continue

            # List/mapping section header: "key:" with no value
            if re.match(r"^(\w+):\s*$", stripped):
                _flush_pending()
                current_key = stripped.rstrip(":").strip()
                list_values = []
                continue

            # Scalar key: value
            kv = re.match(r"^(\w[\w_]*):\s+(.+)$", stripped)
            if kv:
                _flush_pending()
                key, value = kv.group(1).strip(), kv.group(2).strip()
                current_key = key
                if key == "test_framework":
                    report.test_framework = value
                elif key == "test_directory":
                    report.test_directory = value
                elif key == "run_command":
                    report.run_command = value
                elif key == "fixtures_available":
                    report.fixtures_available = value

        # Flush anything left over
        _flush_pending()
        if in_block and current_key == "example_test":
            report.example_test = "\n".join(block_lines).rstrip()

    except Exception:
        logger.exception("Failed to parse context report block; using partial results")

    return report


def _run_exploration_phase(
    session: DockerContainerSession,
    comment_jobs: list[dict],
    instance_dir: Path,
    model: str,
    qwen_auth_type: str | None,
    trajectory: list[dict],
    artifacts: dict[str, str],
) -> ContextReport:
    """Run Phase 1: one Qwen invocation that explores the repo and returns a ContextReport."""
    logger.info("  [Phase 1] Running exploration agent...")
    explore_prompt = _build_exploration_prompt(comment_jobs)
    prompt_path = _write_artifact(
        instance_dir, "explore_prompt.txt", explore_prompt, artifacts
    )
    trajectory.append(
        _trajectory_step(
            "exploration_prompt",
            prompt=explore_prompt,
            artifact_path=prompt_path,
        )
    )

    started = time.time()
    stdout, stderr, rc = invoke_qwen_in_container(
        session, explore_prompt, model, auth_type=qwen_auth_type
    )
    _write_artifact(instance_dir, "explore_stdout.txt", stdout, artifacts)
    _write_artifact(instance_dir, "explore_stderr.txt", stderr, artifacts)
    trajectory.append(
        _trajectory_step(
            "exploration_response",
            returncode=rc,
            elapsed_seconds=time.time() - started,
        )
    )

    context_report = _parse_context_report(stdout)
    context_report_path = instance_dir / "context_report.json"
    context_report_path.write_text(
        json.dumps(
            {
                "test_framework": context_report.test_framework,
                "test_directory": context_report.test_directory,
                "run_command": context_report.run_command,
                "import_status": context_report.import_status,
                "related_test_files": context_report.related_test_files,
                "example_test": context_report.example_test,
                "fixtures_available": context_report.fixtures_available,
            },
            indent=2,
        )
    )
    artifacts["context_report.json"] = str(context_report_path)
    logger.info(
        "  [Phase 1] Done. framework=%s dir=%s related_tests=%d",
        context_report.test_framework,
        context_report.test_directory,
        len(context_report.related_test_files),
    )
    return context_report


# ---------------------------------------------------------------------------
# Phase 2 — generation helpers
# ---------------------------------------------------------------------------


def _strip_before_code_only(prompt: str) -> str:
    """Remove only the '## Full file currently under review' block.

    Unlike _remove_large_context_sections, this keeps '## Relevant current
    diff context' (before_patch_lines) since that is specific per comment.
    The full file content is hoisted to a shared header by _build_generation_prompt.
    """
    return re.sub(
        r"\n## Full file currently under review\n```[^\n]*\n.*?\n```\n",
        "\n",
        prompt,
        flags=re.DOTALL,
    )


def _build_generation_prompt(
    comment_jobs: list[dict],
    context_report: ContextReport,
    seed: str,
    run_index: int,
) -> str:
    """Build a generation prompt with deduplicated shared file context, anti-bias
    rules, and the per-comment embedded prompts (before_patch_lines kept)."""

    # --- shared file context block (each unique file included exactly once) ---
    seen_files: set[str] = set()
    shared_file_sections: list[str] = []
    for job in comment_jobs:
        fp = job["path"]
        before_code = job.get("before_code", "")
        if fp not in seen_files and before_code:
            seen_files.add(fp)
            lang_tag = job.get("language", "")
            shared_file_sections.append(
                f"### /workspace/{fp}\n```{lang_tag}\n{before_code}\n```"
            )

    shared_files_block = (
        "\n\n".join(shared_file_sections)
        if shared_file_sections
        else "(no file contents available)"
    )

    # --- per-comment sections: strip before_code but keep before_patch_lines ---
    sections: list[str] = []
    for job in comment_jobs:
        stripped_prompt = _strip_before_code_only(job["prompt"])
        sections.append(
            f"""### Comment {job["comment_index"]}
Target test file: /workspace/{job["test_filename"]}
Language: {job["language"]}

{stripped_prompt}

If you generate a test for this comment, write the final code to:
/workspace/{job["test_filename"]}
"""
        )
    comment_sections = "\n\n".join(sections)

    # --- context report block ---
    import_status_lines = "\n".join(
        f"  {k}: {v}" for k, v in context_report.import_status.items()
    )
    related_files_str = (
        ", ".join(context_report.related_test_files)
        if context_report.related_test_files
        else "none found"
    )
    example_block = (
        f"```python\n{context_report.example_test}\n```"
        if context_report.example_test
        else "(no example test available)"
    )

    return f"""You are Qwen Code running inside the repository at /workspace.
You are at review time. You do NOT see the resolved/merged code.
Infer the intended fix from each comment's review text, diff hunk, and current code.

## Repository context (pre-explored — do not re-run these checks)
- Test framework: {context_report.test_framework}
- Test directory: {context_report.test_directory}
- Run command: {context_report.run_command}
- Import status:
{import_status_lines if import_status_lines else "  (not checked)"}
- Related test files for reference: {related_files_str}
- Available fixtures: {context_report.fixtures_available}

### Style reference — example existing test from this repo:
{example_block}
Mirror this import style, test function structure, and assertion pattern.

## Shared file context (full source files at HEAD — referenced by all comments below)

{shared_files_block}

## Your inference strategy for this run (run {run_index})
{seed}

## Anti-confirmation-bias rules (follow before writing any code)

### Step A — Identify the reviewer's REAL concern
Before writing a single line of test code, answer these questions in a comment
block at the TOP of every generated test file:

# Validation rationale for comment <N>:
# Reviewer concern: <one sentence — what specific behavior/property did the reviewer want changed?>
# Fails on pre-patch code because: <what exactly is wrong in the current code?>
# Passes only if: <specific condition in the patched code — not just "if the fix is applied">
# Would NOT be fooled by a superficial patch that only: <the simplest wrong fix that would not satisfy this test>

### Step B — Coverage checklist (verify before finalizing each test)
- POSITIVE behavior: assert what SHOULD happen (return value, side effect, raised exception)
- NEGATIVE/ABSENCE: if reviewer said something should be removed or not happen, assert the absence
- EDGE CASE: if reviewer mentioned a specific input or boundary, use it
- PUBLIC API/NAME: if reviewer discussed a specific name or signature, verify it at runtime
- USER-VISIBLE OUTCOME: verify observable runtime behavior, not source-text shape — unless the
  review comment is explicitly about source structure, naming, or style

If any applicable checklist item is not covered, redesign the test.

## Rules
- The per-comment prompts below include full requirements — follow them exactly.
- Do not modify existing repository source files.
- Write one test file per comment to the exact target path shown.
- Run your test with the run command above to verify it executes cleanly.
- The rationale comment block is REQUIRED at the top of every test file.
- If a comment cannot produce a valid executable test, leave its target file absent and explain why.

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


def _merge_run_results(
    all_run_results: list[dict],
    indexed_comments: list[tuple[int, dict]],
    instance_id: str,
    repo: str,
    model: str,
    artifacts: dict[str, str],
    instance_dir: Path,
) -> dict:
    """Pick the best per-comment result across N independent generation runs.

    Priority (highest first):
      1. expected_failure_observed=True AND ground_truth_patch_passed=True
      2. expected_failure_observed=True
      3. test ran without error (current_passed is not None)
      4. test file was generated (test_code is not None)
      5. error result (all runs failed for this comment)
    """

    def _priority(result: dict) -> int:
        efail = result.get("expected_failure_observed") or False
        patch_pass = (result.get("assessment") or {}).get(
            "ground_truth_patch_passed"
        ) or False
        if efail and patch_pass:
            return 4
        if efail:
            return 3
        if result.get("current_passed") is not None:
            return 2
        if result.get("test_code") is not None:
            return 1
        return 0

    # group results by comment_index across runs
    by_comment: dict[int, list[dict]] = {}
    for run_result in all_run_results:
        for r in run_result.get("results", []):
            by_comment.setdefault(r["comment_index"], []).append(r)

    merged_results: list[dict] = []
    for comment_index, _ in indexed_comments:
        candidates = by_comment.get(comment_index, [])
        if not candidates:
            continue
        best = max(candidates, key=_priority)
        # tag which run this came from
        run_idx = next(
            (
                k
                for k, run_result in enumerate(all_run_results)
                for r in run_result.get("results", [])
                if r is best
            ),
            None,
        )
        best = {**best, "run_index": run_idx}
        merged_results.append(best)

    return _finalize_result(
        instance_id=instance_id,
        repo=repo,
        model=model,
        indexed_comments=indexed_comments,
        comment_results=merged_results,
        artifacts=artifacts,
        instance_dir=instance_dir,
    )


def process_instance_multi(
    instance: dict,
    output_dir: Path,
    model: str,
    docker_image: str,
    qwen_settings_path: Path,
    selected_comment_indices: set[int] | None = None,
    num_samples: int = 3,
    skip_execution: bool = False,
    dry_run: bool = False,
) -> dict:
    """Two-phase multi-sample test generation for one instance.

    Phase 1: One exploration agent invocation gathers repository context
             (test framework, related tests, import status, example test).
    Phase 2: num_samples independent generation agent invocations, each
             receiving the shared context and a different diversity seed.
             The container is reset between runs so no test file leaks across.
    """
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
            (ci, c)
            for ci, c in enumerate(all_comments)
            if ci in selected_comment_indices
        ]

    logger.info(
        "process_instance_multi: %s (%d comments, %d samples)",
        instance_id,
        len(indexed_comments),
        num_samples,
    )

    instance_dir = output_dir / instance_id.replace("/", "__")
    instance_dir.mkdir(parents=True, exist_ok=True)

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-agent-testgen-multi-{safe_name}"
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
    all_run_results: list[dict] = []

    def _reset_to_head() -> bool:
        reset_cmd = f"git checkout --force {head_commit} && git clean -fd --quiet"
        r = session.run_command(reset_cmd, timeout=120)
        trajectory.append(
            _trajectory_step(
                "reset_to_head",
                command=reset_cmd,
                returncode=r.returncode,
                stdout=r.stdout,
                stderr=r.stderr,
            )
        )
        if r.returncode != 0:
            logger.error("[%s] git reset failed: %s", instance_id, r.stderr[:300])
            return False
        return True

    def _persist_trajectory() -> str | None:
        return write_agent_trajectory(
            artifact_dir=instance_dir,
            instance=instance,
            model=model,
            agent="qwen-code-multi",
            raw_events=trajectory,
            artifacts=artifacts,
            comment_indices=[ci for ci, _ in indexed_comments],
        )

    try:
        session.start()
        logger.info("Started container %s (image: %s)", container_name, docker_image)
        setup_qwen_in_container(session)

        def get_file_fn(commit: str, filepath: str) -> str:
            r = session.run_command(
                ["git", "show", f"{commit}:{filepath}"], timeout=30
            )
            return r.stdout if r.returncode == 0 else ""

        if not _reset_to_head():
            error = "git checkout failed at startup"
            return _build_all_error_results(
                instance_id, repo, model, indexed_comments, error, instance_dir
            )

        # ---------------------------------------------------------------
        # Build comment_jobs (same logic as process_instance)
        # ---------------------------------------------------------------
        comment_jobs: list[dict] = []
        for _pos, (i, comment) in enumerate(indexed_comments):
            language = (
                test_generator.detect_language(comment["path"])
                or test_generator.DEFAULT_LANGUAGE
            )
            if language not in EXECUTABLE_LANGUAGES:
                continue
            comment_type = test_generator.classify_comment(
                comment["text"], comment.get("diff_hunk", "")
            )
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

        if not comment_jobs:
            logger.warning("[%s] No executable comment jobs; nothing to generate", instance_id)
            _persist_trajectory()
            return _finalize_result(
                instance_id=instance_id,
                repo=repo,
                model=model,
                indexed_comments=indexed_comments,
                comment_results=[],
                artifacts=artifacts,
                instance_dir=instance_dir,
            )

        # ---------------------------------------------------------------
        # Phase 1 — exploration
        # ---------------------------------------------------------------
        context_report = _run_exploration_phase(
            session=session,
            comment_jobs=comment_jobs,
            instance_dir=instance_dir,
            model=model,
            qwen_auth_type=qwen_auth_type,
            trajectory=trajectory,
            artifacts=artifacts,
        )

        if dry_run:
            trajectory.append(
                _trajectory_step("dry_run", message="Stopped after Phase 1 exploration.")
            )
            _persist_trajectory()
            error_results = [
                _make_error_result(
                    job["comment_index"],
                    job["comment"],
                    job["comment_type"],
                    job["language"],
                    "Dry run: exploration done; generation was not invoked",
                )
                for job in comment_jobs
            ]
            return _finalize_result(
                instance_id=instance_id,
                repo=repo,
                model=model,
                indexed_comments=indexed_comments,
                comment_results=error_results,
                artifacts=artifacts,
                instance_dir=instance_dir,
            )

        # ---------------------------------------------------------------
        # Phase 2 — N independent generation runs
        # ---------------------------------------------------------------
        seeds = DIVERSITY_SEEDS[:num_samples]
        for run_index, seed in enumerate(seeds):
            logger.info(
                "  [Phase 2] Run %d/%d (seed: %s...)",
                run_index + 1,
                len(seeds),
                seed[:40],
            )
            _reset_to_head()

            gen_prompt = _build_generation_prompt(
                comment_jobs=comment_jobs,
                context_report=context_report,
                seed=seed,
                run_index=run_index,
            )
            prompt_path = _write_artifact(
                instance_dir,
                f"prompt_run_{run_index}.txt",
                gen_prompt,
                artifacts,
            )
            trajectory.append(
                _trajectory_step(
                    "generation_prompt",
                    run_index=run_index,
                    artifact_path=prompt_path,
                    num_comments=len(comment_jobs),
                )
            )

            started = time.time()
            agent_stdout, agent_stderr, agent_rc = invoke_qwen_in_container(
                session,
                gen_prompt,
                model,
                auth_type=qwen_auth_type,
            )
            _write_artifact(
                instance_dir, f"qwen_stdout_run_{run_index}.txt", agent_stdout, artifacts
            )
            _write_artifact(
                instance_dir, f"qwen_stderr_run_{run_index}.txt", agent_stderr, artifacts
            )
            trajectory.append(
                _trajectory_step(
                    "generation_response",
                    run_index=run_index,
                    returncode=agent_rc,
                    elapsed_seconds=time.time() - started,
                )
            )
            _persist_trajectory()

            # collect + validate + run tests
            run_comment_results: list[dict] = []
            trajectory_path = _persist_trajectory()

            # Pass 1: copy ALL generated test files out of the container BEFORE any
            # execution. test_runner does `git checkout --force && git clean -fd`,
            # which deletes every untracked file in /workspace (including other
            # comments' not-yet-copied test files). Copying first avoids that.
            for job in comment_jobs:
                run_test_filename = f"run_{run_index}_{job['test_filename']}"
                job["_run_test_file"] = (instance_dir / run_test_filename).resolve()
                job["_run_test_file_rel"] = str(Path(instance_dir.name) / run_test_filename)
                job["_run_test_copied"] = _copy_generated_test(
                    session, job["test_filename"], job["_run_test_file"]
                )

            # Pass 2: validate + execute each copied test.
            for job in comment_jobs:
                i = job["comment_index"]
                comment = job["comment"]
                language = job["language"]
                comment_type = job["comment_type"]
                test_file = job["_run_test_file"]
                test_file_rel = job["_run_test_file_rel"]

                if not job["_run_test_copied"]:
                    run_comment_results.append(
                        _make_error_result(
                            i,
                            comment,
                            comment_type,
                            language,
                            f"Run {run_index}: agent did not write expected test file",
                            trajectory_path,
                        )
                    )
                    continue

                test_code = test_file.read_text(encoding="utf-8")
                if not test_generator.validate_test_syntax(test_code, language):
                    run_comment_results.append(
                        {
                            **_make_error_result(
                                i,
                                comment,
                                comment_type,
                                language,
                                f"Run {run_index}: generated test failed syntax validation",
                                trajectory_path,
                            ),
                            "test_file": test_file_rel,
                            "test_code": test_code,
                            "attempts_used": 1,
                        }
                    )
                    continue

                if skip_execution:
                    run_comment_results.append(
                        {
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
                    )
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
                        run_index=run_index,
                        comment_index=i,
                        test_file=job["test_filename"],
                        current_passed=current.current_passed,
                        expected_failure_observed=current.expected_failure_observed,
                        ground_truth_patch_passed=patched.patched_passed,
                    )
                )
                trajectory_path = _persist_trajectory()
                run_comment_results.append(
                    {
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
                )

            run_result = _finalize_result(
                instance_id=instance_id,
                repo=repo,
                model=model,
                indexed_comments=indexed_comments,
                comment_results=run_comment_results,
                artifacts=dict(artifacts),
                instance_dir=instance_dir,
                result_filename=f"result_run_{run_index}.json",
            )
            all_run_results.append(run_result)
            logger.info(
                "  [Phase 2] Run %d done: %d tests, %.1f%% expected-failure rate",
                run_index,
                sum(1 for r in run_comment_results if r.get("test_code")),
                run_result.get("overall_expected_failure_rate", 0.0) * 100,
            )

        # ---------------------------------------------------------------
        # Merge across runs
        # ---------------------------------------------------------------
        merged = _merge_run_results(
            all_run_results=all_run_results,
            indexed_comments=indexed_comments,
            instance_id=instance_id,
            repo=repo,
            model=model,
            artifacts=artifacts,
            instance_dir=instance_dir,
        )
        logger.info(
            "[%s] Multi-run merge done: %d tests, %.1f%% expected-failure rate",
            instance_id,
            sum(1 for r in merged.get("results", []) if r.get("test_code")),
            merged.get("overall_expected_failure_rate", 0.0) * 100,
        )
        return merged

    finally:
        session.remove(force=True)
        logger.info("Removed container %s", container_name)


def _build_all_error_results(
    instance_id: str,
    repo: str,
    model: str,
    indexed_comments: list[tuple[int, dict]],
    error: str,
    instance_dir: Path,
) -> dict:
    """Helper: build a finalized error result for all comments."""
    error_results = []
    for i, comment in indexed_comments:
        language = (
            test_generator.detect_language(comment["path"])
            or test_generator.DEFAULT_LANGUAGE
        )
        error_results.append(
            _make_error_result(i, comment, "unknown", language, error)
        )
    return _finalize_result(
        instance_id=instance_id,
        repo=repo,
        model=model,
        indexed_comments=indexed_comments,
        comment_results=error_results,
        artifacts={},
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
