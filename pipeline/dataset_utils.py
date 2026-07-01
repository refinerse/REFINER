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
