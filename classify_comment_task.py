#!/usr/bin/env python3
"""Classify the edit intent of each review comment in Stage 3 instances.

For each reference_review_comment, reads ±N lines of file context from the
GitHub file cache, adds the other reference comments on the PR plus the
relevant review threads recovered from GitHub (filtered_out_threads.jsonl,
shrunk with heuristics if too long: suggestion blocks stripped, test-file
comments dropped, then truncation), and asks an LLM to reason about why the
reviewer made the comment (trigger / concern / expectation) before assigning
one of five intent labels:
  Refactoring, Bugfix, Logging, Documentation, Others

Results are written to a JSONL file, one record per comment, with per-comment
token/cost tracking and a cumulative cost summary.

Usage:
  python classify_comment_task.py --limit 5
  python classify_comment_task.py --workers 32 --model gpt-4.1-mini
  python classify_comment_task.py --instance Avaiga__taipy-1042@a76a34b
  python classify_comment_task.py --no-resume
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import dotenv
dotenv.load_dotenv()

from tqdm import tqdm

from pipeline.llm_client import LLMError, LLMUsage, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

VALID_LABELS = {"Refactoring", "Bugfix", "Logging", "Documentation", "Others"}

DEFAULT_STAGE3_FILE = Path("results_pipeline_funnel/stage3_testgen_verified.jsonl")
DEFAULT_OUTPUT_FILE = Path("results_pipeline_funnel/comment_intent.jsonl")
DEFAULT_CACHE_DIR = Path("github_file_cache")
DEFAULT_MISSING_THREADS_FILE = Path("comment_recovery/filtered_out_threads.jsonl")
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_WORKERS = 30
DEFAULT_CONTEXT_LINES = 20
DEFAULT_MAX_SECTION_CHARS = 6000
DEFAULT_MAX_RELEVANT_THREADS = 10

SYSTEM_PROMPT = """\
You are an expert code reviewer analyst. You will be shown one code review \
comment from a pull request (the comment to classify), together with the code \
it refers to, the other reference review comments on the same PR, and other \
relevant review threads from the same PR (made up to the commit under review).

First reason about the comment:
1. WHY the reviewer came up with this comment — what in the code or PR \
triggered it (use the other PR comments / relevant threads as context for the \
reviewer's running concerns).
2. What is the reviewer's underlying CONCERN.
3. What is the reviewer's EXPECTATION — the change they expect the author to make.

Then classify the comment's edit intent into exactly one of these five categories:
- Refactoring: Suggestions to improve code structure, readability, or design \
without changing behaviour.
- Bugfix: Identifies a bug or incorrect behaviour and suggests a fix.
- Logging: Suggestions about logging, monitoring, or observability practices.
- Documentation: Recommendations to add or improve comments, docstrings, or docs.
- Others: Unspecified, ambiguous, or does not fit the above categories.

Respond ONLY with a JSON object in this exact format (no markdown, no extra text):
{"why": "<1-2 sentences: what triggered the comment>", \
"concern": "<one sentence: the reviewer's underlying concern>", \
"expectation": "<one sentence: the change the reviewer expects>", \
"label": "<one of the five categories>"}"""


# ---------------------------------------------------------------------------
# File context extraction
# ---------------------------------------------------------------------------

def get_file_context(
    cache_dir: Path,
    repo: str,
    head_commit: str,
    file_path: str,
    target_line: int | None,
    context_lines: int,
) -> tuple[str, bool]:
    """Return (context_text, from_cache).

    Reads ±context_lines lines around target_line from the cached source file.
    Falls back to returning an empty string (caller will use diff_hunk) if the
    file is not in the cache.
    """
    repo_slug = repo.replace("/", "__")
    cached_file = cache_dir / repo_slug / head_commit / file_path

    if not cached_file.exists():
        return "", False

    try:
        lines = cached_file.read_text(errors="replace").splitlines()
    except OSError as e:
        logger.warning("Could not read cache file %s: %s", cached_file, e)
        return "", False

    if target_line is None:
        # No line info — return the whole file truncated to avoid huge prompts
        snippet = lines[:context_lines * 2]
        return "\n".join(f"{i+1:4d} | {l}" for i, l in enumerate(snippet)), True

    # Convert 1-based line number to 0-based index
    idx = target_line - 1
    start = max(0, idx - context_lines)
    end = min(len(lines), idx + context_lines + 1)
    snippet = lines[start:end]
    numbered = "\n".join(f"{start + i + 1:4d} | {l}" for i, l in enumerate(snippet))
    return numbered, True


# ---------------------------------------------------------------------------
# PR comment context sections
# ---------------------------------------------------------------------------

SUGGESTION_BLOCK_RE = re.compile(r"```suggestion.*?```", re.DOTALL)
TEST_PATH_RE = re.compile(r"(^|/)tests?(/|\b)|(^|/|_)test_|_test\.", re.IGNORECASE)


def strip_suggestion_blocks(text: str) -> str:
    return SUGGESTION_BLOCK_RE.sub("[code suggestion removed]", text)


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH_RE.search(path or ""))


def _format_comment_entry(comment: dict) -> str:
    line = comment.get("original_line") or comment.get("line")
    loc = comment.get("path", "?") + (f":{line}" if line else "")
    return f"[{loc}]\n{comment.get('text', '').strip()}"


def build_comments_block(comments: list[dict], max_chars: int) -> str:
    """Render a list of PR comments, progressively shrinking to fit max_chars.

    Reduction order: strip ```suggestion``` blocks -> drop comments on test
    files -> truncate each comment -> drop trailing comments.
    """
    if not comments:
        return "(none)"

    cmts = [dict(c) for c in comments]
    notes: list[str] = []

    def render() -> str:
        parts = [_format_comment_entry(c) for c in cmts]
        if notes:
            parts.append(" ".join(notes))
        return "\n\n".join(parts)

    if len(render()) <= max_chars:
        return render()

    # 1) suggestion blocks are code the reviewer already wrote out — drop them
    for c in cmts:
        c["text"] = strip_suggestion_blocks(c.get("text", ""))
    if len(render()) <= max_chars:
        return render()

    # 2) drop comments on test files
    non_test = [c for c in cmts if not is_test_path(c.get("path", ""))]
    if 0 < len(non_test) < len(cmts):
        notes.append(f"({len(cmts) - len(non_test)} comments on test files omitted.)")
        cmts = non_test
        if len(render()) <= max_chars:
            return render()

    # 3) truncate each comment to an even share of the budget
    per_comment = max(200, max_chars // len(cmts))
    for c in cmts:
        if len(c["text"]) > per_comment:
            c["text"] = c["text"][:per_comment].rstrip() + " [...truncated]"
    if len(render()) <= max_chars:
        return render()

    # 4) drop comments from the end until it fits
    omitted = 0
    while len(cmts) > 1 and len(render()) > max_chars:
        cmts.pop()
        omitted += 1
        notes_tail = f"({omitted} more comments omitted.)"
        notes = [n for n in notes if "more comments" not in n] + [notes_tail]
    return render()


def load_missing_threads(path: Path) -> dict[str, list[dict]]:
    """Load the filtered-out review threads (from fetch_and_compare_pr_comments.py)
    keyed by instance_id."""
    threads: dict[str, list[dict]] = {}
    if not path.exists():
        logger.warning("Missing-threads file %s not found — relevant-comments "
                       "section will be empty", path)
        return threads
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            threads.setdefault(rec["instance_id"], []).append(rec)
    return threads


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_prompt(
    instance_id: str,
    repo: str,
    pr_title: str,
    comment_text: str,
    file_path: str,
    code_context: str,
    diff_hunk: str,
    from_cache: bool,
    pr_comments_block: str,
    relevant_comments_block: str,
) -> list[dict]:
    """Build the messages list for the LLM classification call."""
    if from_cache and code_context:
        context_block = f"**File context (±{DEFAULT_CONTEXT_LINES} lines around comment):**\n```\n{code_context}\n```"
    else:
        context_block = f"**Diff hunk (code being reviewed):**\n```\n{diff_hunk}\n```"

    user_content = f"""\
Repository: `{repo}`
PR title: {pr_title}
File: `{file_path}`

{context_block}

**Reviewer comment to classify:**
{comment_text}

**Other reference comments on this PR:**
{pr_comments_block}

**Relevant comments (other review threads on this PR, up to the commit under review):**
{relevant_comments_block}"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# LLM call + response parsing
# ---------------------------------------------------------------------------

def classify_comment(messages: list[dict], model: str) -> tuple[dict, LLMUsage, str]:
    """Call the LLM and parse the analysis. Returns (analysis, usage, raw_output)
    where analysis has keys: why, concern, expectation, label."""
    # generous cap: reasoning models (e.g. qwen plus) spend tokens thinking
    # before emitting the JSON; too small a cap yields empty content
    response = chat(messages, model=model, max_tokens=4096)
    raw_output = response.text
    text = raw_output.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    analysis = {"why": "", "concern": "", "expectation": "", "label": "Others"}
    try:
        parsed = json.loads(text)
        for key in ("why", "concern", "expectation"):
            analysis[key] = parsed.get(key, "")
        label = parsed.get("label", "Others")
        if label not in VALID_LABELS:
            logger.warning("Unexpected label %r — defaulting to Others", label)
            label = "Others"
        analysis["label"] = label
    except json.JSONDecodeError:
        logger.warning("Could not parse LLM response as JSON: %r", text[:200])
        analysis["why"] = text[:300]

    return analysis, response.usage, raw_output


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_stage3_instances(stage3_file: Path) -> list[dict]:
    instances = []
    with stage3_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            instances.append(json.loads(line))
    return instances


def load_existing_results(output_file: Path) -> set[tuple[str, int]]:
    """Return set of (instance_id, comment_index) already classified."""
    done: set[tuple[str, int]] = set()
    if not output_file.exists():
        return done
    with output_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                done.add((rec["instance_id"], rec["comment_index"]))
            except (json.JSONDecodeError, KeyError):
                pass
    return done


# ---------------------------------------------------------------------------
# Per-comment task
# ---------------------------------------------------------------------------

def process_comment(
    instance: dict,
    comment_index: int,
    comment: dict,
    cache_dir: Path,
    model: str,
    context_lines: int,
    missing_threads: list[dict],
    max_section_chars: int,
) -> dict:
    """Classify one comment. Returns the output record dict."""
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    pr_title = instance.get("title", "")
    head_commit = instance["commit_to_review"]["head_commit"]

    file_path = comment["path"]
    comment_text = comment["text"]
    diff_hunk = comment.get("diff_hunk", "")

    # Prefer original_start_line, fall back to original_line
    target_line = comment.get("original_start_line") or comment.get("original_line")

    code_context, from_cache = get_file_context(
        cache_dir, repo, head_commit, file_path, target_line, context_lines
    )

    other_pr_comments = [
        c
        for i, c in enumerate(instance["reference_review_comments"])
        if i != comment_index
    ]
    pr_comments_block = build_comments_block(other_pr_comments, max_section_chars)

    # cap the relevant threads at the N most recent, shown in chronological order
    if len(missing_threads) > DEFAULT_MAX_RELEVANT_THREADS:
        missing_threads = sorted(
            missing_threads, key=lambda t: t.get("root_created_at") or ""
        )[-DEFAULT_MAX_RELEVANT_THREADS:]
    relevant_comments_block = build_comments_block(missing_threads, max_section_chars)

    messages = build_prompt(
        instance_id=instance_id,
        repo=repo,
        pr_title=pr_title,
        comment_text=comment_text,
        file_path=file_path,
        code_context=code_context,
        diff_hunk=diff_hunk,
        from_cache=from_cache,
        pr_comments_block=pr_comments_block,
        relevant_comments_block=relevant_comments_block,
    )

    analysis, usage, raw_output = classify_comment(messages, model)

    return {
        "instance_id": instance_id,
        "comment_index": comment_index,
        "path": file_path,
        "label": analysis["label"],
        "why": analysis["why"],
        "concern": analysis["concern"],
        "expectation": analysis["expectation"],
        "context_source": "cache" if from_cache else "diff_hunk",
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "cost_usd": usage.cost_usd,
        "raw_prompt": messages,
        "raw_output": raw_output,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Classify review comment edit intent.")
    parser.add_argument("--input", type=Path, default=DEFAULT_STAGE3_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--missing-threads", type=Path, default=DEFAULT_MISSING_THREADS_FILE,
                        help="JSONL of filtered-out review threads (from fetch_and_compare_pr_comments.py)")
    parser.add_argument("--max-section-chars", type=int, default=DEFAULT_MAX_SECTION_CHARS,
                        help="Char budget for each PR-comments context section before reduction heuristics kick in")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--context-lines", type=int, default=DEFAULT_CONTEXT_LINES)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--limit", type=int, default=None, help="Process only N instances")
    parser.add_argument("--instance", type=str, default=None, help="Process a single instance ID")
    parser.add_argument("--no-resume", action="store_true", help="Re-classify all, ignoring existing output")
    args = parser.parse_args()

    instances = load_stage3_instances(args.input)
    logger.info("Loaded %d instances from %s", len(instances), args.input)

    missing_threads_by_instance = load_missing_threads(args.missing_threads)
    logger.info(
        "Loaded missing threads for %d instances from %s",
        len(missing_threads_by_instance),
        args.missing_threads,
    )

    if args.instance:
        instances = [i for i in instances if i["instance_id"] == args.instance]
        if not instances:
            logger.error("Instance %r not found", args.instance)
            sys.exit(1)

    if args.limit:
        instances = instances[: args.limit]

    # Build full work list: (instance, comment_index, comment)
    work: list[tuple[dict, int, dict]] = []
    for inst in instances:
        for idx, comment in enumerate(inst["reference_review_comments"]):
            work.append((inst, idx, comment))

    logger.info("Total comments to classify: %d", len(work))

    # Resume: skip already-classified pairs
    done_keys: set[tuple[str, int]] = set()
    if not args.no_resume:
        done_keys = load_existing_results(args.output)
        if done_keys:
            logger.info("Resuming — skipping %d already classified comments", len(done_keys))

    pending = [
        (inst, idx, comment)
        for inst, idx, comment in work
        if (inst["instance_id"], idx) not in done_keys
    ]
    logger.info("%d comments pending classification", len(pending))

    if not pending:
        logger.info("Nothing to do.")
        return

    # Thread-safe state
    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    total_usage = LLMUsage()
    classified_count = 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Truncate output file when not resuming so old records don't accumulate
    if args.no_resume and args.output.exists():
        args.output.unlink()

    def submit(inst: dict, idx: int, comment: dict) -> dict:
        return process_comment(
            instance=inst,
            comment_index=idx,
            comment=comment,
            cache_dir=args.cache_dir,
            model=args.model,
            context_lines=args.context_lines,
            missing_threads=missing_threads_by_instance.get(inst["instance_id"], []),
            max_section_chars=args.max_section_chars,
        )

    with args.output.open("a") as out_f:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(submit, inst, idx, comment): (inst["instance_id"], idx)
                       for inst, idx, comment in pending}

            with tqdm(total=len(futures), unit="comment", desc="Classifying") as pbar:
                for future in as_completed(futures):
                    inst_id, idx = futures[future]
                    try:
                        record = future.result()
                    except (LLMError, Exception) as e:
                        kind = "LLM error" if isinstance(e, LLMError) else "Error"
                        logger.error("%s for %s comment %d: %s", kind, inst_id, idx, e)
                        record = {
                            "instance_id": inst_id,
                            "comment_index": idx,
                            "path": "",
                            "label": "Others",
                            "why": f"{kind}: {e}",
                            "concern": "",
                            "expectation": "",
                            "context_source": "error",
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "cost_usd": 0.0,
                            "raw_prompt": None,
                            "raw_output": None,
                        }

                    with write_lock:
                        out_f.write(json.dumps(record) + "\n")
                        out_f.flush()

                    with cost_lock:
                        nonlocal_usage = LLMUsage(
                            prompt_tokens=record["prompt_tokens"],
                            completion_tokens=record["completion_tokens"],
                            total_tokens=record["prompt_tokens"] + record["completion_tokens"],
                            cost_usd=record["cost_usd"],
                        )
                        total_usage = total_usage + nonlocal_usage
                        classified_count += 1

                    pbar.update(1)
                    pbar.set_postfix(cost=f"${total_usage.cost_usd:.4f}")

    # Write cost summary alongside the output file
    cost_summary_path = args.output.with_name(args.output.stem + "_cost_summary.json")
    summary = {
        "total_comments": len(work),
        "classified": classified_count + len(done_keys),
        "newly_classified": classified_count,
        "model": args.model,
        **total_usage.to_dict(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cost_summary_path.write_text(json.dumps(summary, indent=2))

    logger.info(
        "Done. Classified %d comments. Total cost: $%.4f (%d tokens)",
        classified_count,
        total_usage.cost_usd,
        total_usage.total_tokens,
    )
    logger.info("Results: %s", args.output)
    logger.info("Cost summary: %s", cost_summary_path)


if __name__ == "__main__":
    main()
