"""Dataset loading utilities backed by the local JSONL dataset file.

Provides functions to load individual instances or filtered batches from the
workspace-local `dataset/instances.jsonl` file.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DATASET_FILE = Path(__file__).resolve().parent.parent / "dataset" / "instances.jsonl"
_dataset_cache: list[dict] | None = None


def _get_dataset():
    """Load and cache the local dataset JSONL file."""
    global _dataset_cache
    if _dataset_cache is None:
        logger.info("Loading local dataset from %s...", DEFAULT_DATASET_FILE)
        rows: list[dict] = []
        with DEFAULT_DATASET_FILE.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        _dataset_cache = rows
        logger.info("Loaded %d local instances.", len(_dataset_cache))
    return _dataset_cache


def load_instance(instance_id: str) -> dict | None:
    """Load a single instance by its instance_id.

    Returns:
        The instance dict, or None if not found.
    """
    ds = _get_dataset()
    for row in ds:
        if row["instance_id"] == instance_id:
            return row
    logger.warning("Instance '%s' not found in local dataset", instance_id)
    return None


def load_instances(
    repo: str | None = None,
    difficulty: str | None = None,
    max_comments: int | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Load instances with optional filtering.

    Args:
        repo: Filter by repository name (e.g. 'tobymao/sqlglot').
        difficulty: Filter by difficulty level.
        max_comments: Only include instances with at most this many comments.
        limit: Maximum number of instances to return.

    Returns:
        List of instance dicts matching the filters.
    """
    ds = _get_dataset()
    results = []

    for row in ds:
        if repo and row["repo"] != repo:
            continue
        if difficulty and row["metadata"]["difficulty"] != difficulty:
            continue
        if max_comments is not None:
            if len(row["reference_review_comments"]) > max_comments:
                continue
        results.append(row)
        if limit and len(results) >= limit:
            break

    logger.info(
        "Filtered %d local instances (repo=%s, difficulty=%s, limit=%s)",
        len(results), repo, difficulty, limit,
    )
    return results


def get_instance_summary(instance: dict) -> str:
    """Return a human-readable one-line summary of an instance."""
    meta = instance["metadata"]
    num_comments = len(instance["reference_review_comments"])
    return (
        f"{instance['instance_id']} | "
        f"{instance['repo']} | "
        f"{meta['difficulty']} | "
        f"{num_comments} comment(s) | "
        f"{meta['problem_domain']}"
    )


COMMENT_MARKER = "  <-- [REVIEW COMMENT]"


def mark_commented_lines(comment: dict) -> str:
    """Return the comment's diff_hunk with the commented line(s) suffixed by COMMENT_MARKER.

    GitHub trims diff_hunk so it ends at the commented line; a multi-line comment
    extends back to ``original_start_line`` (matched against the line's own side).
    """
    import re

    hunk = comment.get("diff_hunk") or ""
    lines = hunk.split("\n")
    header = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", lines[0])
    if not header or len(lines) < 2:
        return hunk
    old, new = int(header[1]), int(header[2])
    numbers = [None]  # per-line number on its own side; header has none
    for ln in lines[1:]:
        if ln.startswith("-"):
            numbers.append(old); old += 1
        elif ln.startswith("+"):
            numbers.append(new); new += 1
        elif ln.startswith("\\"):
            numbers.append(None)
        else:
            numbers.append(new); old += 1; new += 1
    last = max(i for i, n in enumerate(numbers) if n is not None)
    first = last
    start = comment.get("original_start_line")
    if start:
        for i in range(last, 0, -1):
            if numbers[i] == start:
                first = i
                break
    return "\n".join(
        ln + COMMENT_MARKER if first <= i <= last and numbers[i] is not None else ln
        for i, ln in enumerate(lines)
    )


if __name__ == "__main__":
    h = "@@ -10,3 +10,4 @@ def f():\n a\n-b\n+c\n+d"
    assert mark_commented_lines({"diff_hunk": h}).endswith("+d" + COMMENT_MARKER)
    out = mark_commented_lines({"diff_hunk": h, "original_start_line": 11}).split("\n")
    assert [l.endswith(COMMENT_MARKER) for l in out] == [False, False, False, True, True], out
    assert mark_commented_lines({"diff_hunk": ""}) == ""
    print("ok")
