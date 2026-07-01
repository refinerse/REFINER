#!/usr/bin/env python3
"""Compare result folders with automatically detected test result formats.

Writes a CSV with one row per instance and prints a compact summary table.

By default this compares:
  - pure_qwen_replay_2
  - results_agent_resolution_vt_sk_merged

For results with groundtruth_assessment, test outcomes are read from:
  groundtruth_assessment.results[].passed

For other results, test outcomes are read from:
  results[].test_passed
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    import patch_similarity as ps
except ImportError:
    # Only required when --similarity is requested.
    ps = None

try:
    import report_eval_on_split as rep
except ImportError:
    # Only required for the split-eval (patch-verification) metric rows.
    rep = None


DEFAULT_RESULT_DIRS = [
    Path("agents_results/pure_qwen_3.6_plus"),
    Path("agents_results/pure_qwen_3.6_plus_with_task"),
    Path("agents_results/pure_qwen_3.6_plus_with_validation_test"),
    Path("agents_results/pure_qwen_3.6_plus_with_task_and_validation_test"),
    Path("agents_results/icse_intention"),
    Path("agents_results/icse_intention_with_3.6_flash"),
    Path("agents_results/icse_intention_with_4.6_sonnet"),
    Path("agents_results/pure_qwen_3.6_flash_baseline"),
    Path("agents_results/pure_qwen_3.6_flash_with_task"),
    Path("agents_results/pure_qwen_3.6_flash_with_validation_test"),
    Path("agents_results/pure_qwen_3.6_flash_with_task_and_validation_test"),
    Path("agents_results/pure_claude_code"),
    Path("agents_results/claude_with_task_and_validation_test"),
    Path("agents_results/claude_with_task"),
    Path("agents_results/claude_with_validation_test"),
]

SHORT_LABELS = [
    "pure_qwen_3.6_plus",
    "pure_qwen_3.6_plus with task",
    "pure_qwen_3.6_plus with validation test",
    "pure_qwen_3.6_plus with task and validation test",
    "icse intention",
    "icse intention with 3.6 flash",
    "icse intention with 4.6 sonnet",
    "pure_qwen_3.6_flash baseline",
    "pure_qwen_3.6_flash with task",
    "pure_qwen_3.6_flash with validation test",
    "pure_qwen_3.6_flash with task and validation test",
    "pure claude code",
    "claude with task and validation test",
    "claude with task",
    "claude with validation test",
]

# Each compare label -> its patch-verification folder under
# evaluate_agent_patch_on_split/ (the source of report_eval_on_split.py metrics).
SPLIT_EVAL_ROOT = Path("evaluate_agent_patch_on_split")
SPLIT_EVAL_FOLDERS = {
    "pure_qwen_3.6_plus": "pure_qwen_3.6_plus",
    "pure_qwen_3.6_plus with task": "pure_qwen_3.6_plus_with_task",
    "pure_qwen_3.6_plus with validation test": "pure_qwen_3.6_plus_with_validation_test",
    "pure_qwen_3.6_plus with task and validation test": "pure_qwen_3.6_plus_with_task_and_validation_test",
    "icse intention": "icse_intention",
    "icse intention with 3.6 flash": "icse_intention_with_3.6_flash",
    "icse intention with 4.6 sonnet": "icse_intention_with_4.6_sonnet",
    "pure_qwen_3.6_flash baseline": "pure_qwen_3.6_flash_baseline",
    "pure_qwen_3.6_flash with task": "pure_qwen_3.6_flash_with_task",
    "pure_qwen_3.6_flash with validation test": "pure_qwen_3.6_flash_with_validation_test",
    "pure_qwen_3.6_flash with task and validation test": "pure_qwen_3.6_flash_with_task_and_validation_test",
    "pure claude code": "pure_claude_code",
    "claude with task and validation test": "claude_with_task_and_validation_test",
    "claude with task": "claude_with_task",
    "claude with validation test": "claude_with_validation_test",
}

DEFAULT_OUTPUT_CSV = Path(f"{DEFAULT_RESULT_DIRS[0]}/compare.csv")
MISSING = "NA"
DATASET_FILE = Path("dataset/instances.jsonl")
DEFAULT_REPOS_DIR = ps.DEFAULT_REPOS_DIR if ps else Path("/data/Documents/crab-dataset/crab-dataset/repos")
# Patch-similarity metrics (agent patch vs human merged_patch, commented files only).
SIMILARITY_METRICS = (
    ("file_bleu", "bleu", "file"),
    ("file_edit_sim", "edit_similarity", "file"),
    ("func_bleu", "bleu", "function"),
    ("func_edit_sim", "edit_similarity", "function"),
)
DEFAULT_MISSING_INSTANCES_DIR = Path("missing_instances")

# Groundtruth comment-intent labels, used for the per-comment-type pass-rate rows.
COMMENT_INTENT_GT_FILE = Path("dataset/comment_task_gt.jsonl")
# Order shown in the summary tables (any type absent from the data is dropped).
COMMENT_TYPES = ("Bugfix", "Refactoring", "Documentation", "Logging", "Others")

# Groundtruth per-comment assertion counts, used for the assertion-bucket pass-rate
# rows. Each result.json under here reports num_assertions per comment_index; this
# count is a property of the (fixed) groundtruth test, the same for every method.
GT_ASSERTION_DIR = Path("results_gt_validation_splitted")
# Buckets of comments by assertion count, in display order (label -> predicate).
ASSERTION_BUCKETS = (
    ("0-1 asserts", lambda n: n <= 1),
    ("2 asserts", lambda n: n == 2),
    ("3-4 asserts", lambda n: 3 <= n <= 4),
    ("5+ asserts", lambda n: n >= 5),
)

# Instance difficulty (from dataset metadata), used for the per-difficulty
# pass-rate rows. A comment inherits its instance's difficulty. Display order; any
# level absent from the data is dropped.
DIFFICULTY_LEVELS = ("low", "medium", "high")

# Each method's token/cost total = main agent trajectory + (if it uses edit
# intents) the intent-classification stage + (if it generates validation tests)
# the test-generation stage. Within a method every stage uses the SAME model
# family, so the per-stage token counts can be merged and priced together at
# that method's AGENT_MODEL rate (verified: token x price reproduces the stored
# claude cost_usd exactly).
#
# label -> intent-classification JSONL consumed by that method.
INTENT_FILE = {
    "pure_qwen_3.6_plus with task": Path("task_classification/comment_task_qwen.jsonl"),
    "pure_qwen_3.6_plus with task and validation test": Path("task_classification/comment_task_qwen.jsonl"),
    "pure_qwen_3.6_flash with task and validation test": Path("task_classification/comment_task_qwen36flash.jsonl"),
    "claude with task and validation test": Path("results_pipeline_funnel/comment_intent_claude_merged.jsonl"),
}
# label -> validation-test-generation result dir consumed by that method.
TESTGEN_DIR = {
    "pure_qwen_3.6_plus with validation test": Path("agents_results/results_testgen_qwen_3.6_plus"),
    "pure_qwen_3.6_plus with task and validation test": Path("agents_results/results_testgen_qwen_3.6_plus"),
    "pure_qwen_3.6_flash with task and validation test": Path("agents_results/results_testgen_qwen_3.6_flash"),
    "claude with task and validation test": Path("agents_results/results_testgen_claude_sonnet_4.6"),
}
# label -> model family of the method (selects the price table below).
AGENT_MODEL = {
    "pure_qwen_3.6_plus": "qwen-plus",
    "pure_qwen_3.6_plus with task": "qwen-plus",
    "pure_qwen_3.6_plus with validation test": "qwen-plus",
    "pure_qwen_3.6_plus with task and validation test": "qwen-plus",
    "icse intention": "qwen-plus",
    "icse intention with 3.6 flash": "qwen-flash",
    "icse intention with 4.6 sonnet": "claude-sonnet-4-6",
    "pure_qwen_3.6_flash baseline": "qwen-flash",
    "pure_qwen_3.6_flash with task and validation test": "qwen-flash",
    "pure claude code": "claude-sonnet-4-6",
    "claude with task and validation test": "claude-sonnet-4-6",
    "claude with task": "claude-sonnet-4-6",
    "claude with validation test": "claude-sonnet-4-6",
}
INPUT_TOKEN_KEYS = ("input_token", "input_tokens", "inputToken", "inputTokens")
OUTPUT_TOKEN_KEYS = ("output_token", "output_tokens", "outputToken", "outputTokens")
CACHE_READ_INPUT_TOKEN_KEYS = (
    "cache_read_input_token",
    "cache_read_input_tokens",
    "cacheReadInputToken",
    "cacheReadInputTokens",
)
CACHE_CREATION_INPUT_TOKEN_KEYS = (
    "cache_creation_input_token",
    "cache_creation_input_tokens",
    "cacheCreationInputToken",
    "cacheCreationInputTokens",
)
COST_KEYS = ("cost", "total_cost", "totalCost")
PROMPT_TOKEN_KEYS = ("prompt_token", "prompt_tokens", "promptToken", "promptTokens")
COMPLETION_TOKEN_KEYS = (
    "completion_token",
    "completion_tokens",
    "completionToken",
    "completionTokens",
)
COST_USD_KEYS = ("cost_usd", "costUsd")

# USD per 1M tokens, per model family. Keys: input (uncached prompt), output,
# cache_creation (cache write), cache_read (cache hit).
#   qwen-plus  : the project's existing DashScope rates (unchanged).
#   qwen-flash : qwen3.6-flash list price (Intl/Singapore) $0.19 in / $1.13 out;
#                cache read = 10% of input and cache write = 1.25x input, the
#                same ratios the qwen-plus row uses.
#   claude-sonnet-4-6 : Anthropic list price $3 in / $15 out / $3.75 cache-write
#                (5m) / $0.30 cache-read (verified to reproduce stored cost_usd).
PRICES: dict[str, dict[str, float]] = {
    "qwen-plus": {"input": 0.325, "output": 1.95, "cache_creation": 0.4063, "cache_read": 0.0325},
    "qwen-flash": {"input": 0.19, "output": 1.13, "cache_creation": 0.2375, "cache_read": 0.019},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_creation": 3.75, "cache_read": 0.30},
}
DEFAULT_PRICE_MODEL = "qwen-plus"


def load_result_index(root: Path) -> dict[str, dict]:
    """Load every result.json under a directory, keyed by instance_id."""
    index: dict[str, dict] = {}
    for result_file in sorted(root.rglob("result.json")):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: Could not read {result_file}: {exc}")
            continue

        instance_id = data.get("instance_id") or result_file.parent.name
        index[instance_id] = data

    return index


def get_numeric_value(data: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue

    return None


def collect_usage_stats(data) -> dict:
    """Sum token/cost usage blocks from a trajectory payload."""
    totals = {
        "input_tokens": 0.0,
        "output_tokens": 0.0,
        "cache_read_input_tokens": 0.0,
        "cache_creation_input_tokens": 0.0,
        "cost": 0.0,
    }
    found = {
        "input_tokens": False,
        "output_tokens": False,
        "cache_read_input_tokens": False,
        "cache_creation_input_tokens": False,
        "cost": False,
    }

    def visit(value) -> None:
        if isinstance(value, dict):
            usage = value.get("usage")
            if isinstance(usage, dict):
                input_tokens = get_numeric_value(usage, INPUT_TOKEN_KEYS)
                output_tokens = get_numeric_value(usage, OUTPUT_TOKEN_KEYS)
                cache_read_input_tokens = get_numeric_value(usage, CACHE_READ_INPUT_TOKEN_KEYS)
                cache_creation_input_tokens = get_numeric_value(usage, CACHE_CREATION_INPUT_TOKEN_KEYS)
                cost = get_numeric_value(usage, COST_KEYS)

                if input_tokens is not None:
                    totals["input_tokens"] += input_tokens
                    found["input_tokens"] = True
                if output_tokens is not None:
                    totals["output_tokens"] += output_tokens
                    found["output_tokens"] = True
                if cache_read_input_tokens is not None:
                    totals["cache_read_input_tokens"] += cache_read_input_tokens
                    found["cache_read_input_tokens"] = True
                if cache_creation_input_tokens is not None:
                    totals["cache_creation_input_tokens"] += cache_creation_input_tokens
                    found["cache_creation_input_tokens"] = True
                if cost is not None:
                    totals["cost"] += cost
                    found["cost"] = True

            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(data)
    return {key: totals[key] for key, was_found in found.items() if was_found}


def collect_top_level_usage_stats(data) -> dict:
    """Stats from a single top-level OpenAI-style usage block, if present.

    Some result folders (e.g. icse_intention / results_intention_rag) store one
    aggregate ``usage`` dict at the trajectory root using prompt/completion token
    keys, instead of the per-message Anthropic-style usage blocks walked by
    ``collect_usage_stats``. Reading that aggregate directly avoids double-counting
    the per-turn usage blocks (which sum to the same total). Returns {} when no
    such top-level usage is present.
    """
    if not isinstance(data, dict):
        return {}
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return {}

    stats: dict = {}
    input_tokens = get_numeric_value(usage, INPUT_TOKEN_KEYS + PROMPT_TOKEN_KEYS)
    output_tokens = get_numeric_value(usage, OUTPUT_TOKEN_KEYS + COMPLETION_TOKEN_KEYS)
    cache_read_input_tokens = get_numeric_value(usage, CACHE_READ_INPUT_TOKEN_KEYS)
    cache_creation_input_tokens = get_numeric_value(usage, CACHE_CREATION_INPUT_TOKEN_KEYS)
    cost = get_numeric_value(usage, COST_KEYS + COST_USD_KEYS)

    if input_tokens is not None:
        stats["input_tokens"] = input_tokens
    if output_tokens is not None:
        stats["output_tokens"] = output_tokens
    if cache_read_input_tokens is not None:
        stats["cache_read_input_tokens"] = cache_read_input_tokens
    if cache_creation_input_tokens is not None:
        stats["cache_creation_input_tokens"] = cache_creation_input_tokens
    if cost is not None:
        stats["cost"] = cost

    return stats


def collect_turns_usage(data) -> dict:
    """Token usage for agent trajectories shaped as
    ``{"turns": [{"agent_stdout_raw", "agent_stdout_parsed"}, ...]}``.

    Each turn's ``agent_stdout_parsed`` holds the per-API-call messages AND a
    trailing aggregate ``usage`` block that already sums them. A naive tree walk
    (``collect_usage_stats``) counts BOTH, double-counting every token; here we
    read only the aggregate, falling back to summing the per-call
    ``message.usage`` blocks when no aggregate is present.

    Turns whose ``agent_stdout_raw`` is byte-identical are the same single agent
    run replicated across comment slots (a recording artifact of the merged
    folders), so each distinct run is counted once.

    Returns {} when the payload is not in this shape, so callers can fall back.
    """
    if not isinstance(data, dict):
        return {}
    turns = data.get("turns")
    if not isinstance(turns, list):
        return {}

    totals = {
        "input_tokens": 0.0,
        "output_tokens": 0.0,
        "cache_read_input_tokens": 0.0,
        "cache_creation_input_tokens": 0.0,
        "cost": 0.0,
    }
    found = dict.fromkeys(totals, False)
    seen_runs: set[str] = set()

    def add_usage(usage: dict) -> None:
        for target_key, keys in (
            ("input_tokens", INPUT_TOKEN_KEYS),
            ("output_tokens", OUTPUT_TOKEN_KEYS),
            ("cache_read_input_tokens", CACHE_READ_INPUT_TOKEN_KEYS),
            ("cache_creation_input_tokens", CACHE_CREATION_INPUT_TOKEN_KEYS),
            ("cost", COST_KEYS),
        ):
            value = get_numeric_value(usage, keys)
            if value is not None:
                totals[target_key] += value
                found[target_key] = True

    saw_turn_usage = False
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        raw = turn.get("agent_stdout_raw")
        if isinstance(raw, str) and raw:
            if raw in seen_runs:
                continue
            seen_runs.add(raw)
        parsed = turn.get("agent_stdout_parsed")
        if not isinstance(parsed, list):
            continue
        # Trailing aggregate usage blocks carry ``usage`` directly (not nested
        # under a ``message``); they already sum that turn's per-call usage.
        aggregates = [
            item["usage"]
            for item in parsed
            if isinstance(item, dict)
            and isinstance(item.get("usage"), dict)
            and "message" not in item
        ]
        if aggregates:
            saw_turn_usage = True
            for usage in aggregates:
                add_usage(usage)
        else:
            for item in parsed:
                if isinstance(item, dict) and isinstance(item.get("message"), dict):
                    usage = item["message"].get("usage")
                    if isinstance(usage, dict):
                        saw_turn_usage = True
                        add_usage(usage)

    if not saw_turn_usage:
        return {}
    return {key: totals[key] for key, was_found in found.items() if was_found}


def load_stats_index(root: Path) -> dict[str, dict]:
    """Load trajectory stats keyed by instance_id."""
    index: dict[str, dict] = {}
    for trajectory_file in sorted(root.rglob("trajectory.json")):
        try:
            data = json.loads(trajectory_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: Could not read {trajectory_file}: {exc}")
            continue

        stats = data.get("stats")
        if not isinstance(stats, dict):
            # Prefer a top-level aggregate usage block when present (icse_intention
            # format), then the per-turn aggregate blocks (agent trajectories, which
            # would otherwise be double-counted by the generic walk), and finally
            # fall back to summing every per-message usage block in the tree.
            stats = (
                collect_top_level_usage_stats(data)
                or collect_turns_usage(data)
                or collect_usage_stats(data)
            )
        if not stats:
            continue

        instance_id = data.get("instance_id") or trajectory_file.parent.name
        index[str(instance_id)] = stats

    return index


def load_testgen_stats_index(root: Path) -> dict[str, dict]:
    """Load validation-test generation usage stats keyed by instance_id."""
    index: dict[str, dict] = {}
    for result_file in sorted(root.rglob("result.json")):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: Could not read {result_file}: {exc}")
            continue

        usage = data.get("usage")
        if not isinstance(usage, dict):
            continue

        stats = {}
        input_tokens = get_numeric_value(usage, PROMPT_TOKEN_KEYS)
        output_tokens = get_numeric_value(usage, COMPLETION_TOKEN_KEYS)
        cost = get_numeric_value(usage, COST_USD_KEYS)

        if input_tokens is not None:
            stats["input_tokens"] = input_tokens
        if output_tokens is not None:
            stats["output_tokens"] = output_tokens
        if cost is not None:
            stats["cost"] = cost
        if not stats:
            continue

        instance_id = data.get("instance_id") or result_file.parent.name
        index[str(instance_id)] = stats

    return index


def add_stat_value(target: dict, source: dict, target_key: str, source_keys: tuple[str, ...]) -> None:
    value = get_numeric_value(source, source_keys)
    if value is None:
        return
    target[target_key] = (get_numeric_value(target, (target_key,)) or 0.0) + value


def merge_extra_stats(stats_index: dict[str, dict], extra_stats_index: dict[str, dict]) -> None:
    for instance_id, extra_stats in extra_stats_index.items():
        stats = stats_index.setdefault(instance_id, {})
        add_stat_value(stats, extra_stats, "input_tokens", INPUT_TOKEN_KEYS)
        add_stat_value(stats, extra_stats, "output_tokens", OUTPUT_TOKEN_KEYS)
        add_stat_value(stats, extra_stats, "cache_read_input_tokens", CACHE_READ_INPUT_TOKEN_KEYS)
        add_stat_value(stats, extra_stats, "cache_creation_input_tokens", CACHE_CREATION_INPUT_TOKEN_KEYS)
        add_stat_value(stats, extra_stats, "cost", COST_KEYS)


def load_comment_intent_stats_index(path: Path) -> dict[str, dict]:
    """Load edit-intent classification usage stats keyed by instance_id."""
    index: dict[str, dict] = {}
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: Could not read comment intent file {path}: {exc}")
        return index

    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: Could not parse {path}:{line_number}: {exc}")
                continue

            instance_id = data.get("instance_id")
            if instance_id is None:
                print(f"WARNING: Missing instance_id in {path}:{line_number}")
                continue

            stats = index.setdefault(str(instance_id), {})
            add_stat_value(stats, data, "input_tokens", PROMPT_TOKEN_KEYS)
            add_stat_value(stats, data, "output_tokens", COMPLETION_TOKEN_KEYS)

    return index


def merge_stage_stats(stats_indexes: list[dict[str, dict]], labels: list[str]) -> None:
    """Fold each method's intent-classification and test-generation token usage
    into its agent stats, per the INTENT_FILE / TESTGEN_DIR maps. Distinct
    sources are loaded once and reused across methods that share them."""
    testgen_cache: dict[Path, dict[str, dict]] = {}
    intent_cache: dict[Path, dict[str, dict]] = {}
    for label, stats_index in zip(labels, stats_indexes, strict=True):
        testgen_dir = TESTGEN_DIR.get(label)
        if testgen_dir is not None:
            if testgen_dir not in testgen_cache:
                testgen_cache[testgen_dir] = load_testgen_stats_index(testgen_dir)
            merge_extra_stats(stats_index, testgen_cache[testgen_dir])
        intent_file = INTENT_FILE.get(label)
        if intent_file is not None:
            if intent_file not in intent_cache:
                intent_cache[intent_file] = load_comment_intent_stats_index(intent_file)
            merge_extra_stats(stats_index, intent_cache[intent_file])


def load_dataset_instance_ids(path: Path) -> list[str]:
    """Load expected instance IDs from the dataset JSONL file."""
    instance_ids: list[str] = []
    seen: set[str] = set()
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: Could not read dataset file {path}: {exc}")
        return instance_ids

    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: Could not parse {path}:{line_number}: {exc}")
                continue

            instance_id = data.get("instance_id")
            if instance_id is None:
                print(f"WARNING: Missing instance_id in {path}:{line_number}")
                continue

            instance_id = str(instance_id)
            if instance_id not in seen:
                instance_ids.append(instance_id)
                seen.add(instance_id)

    return instance_ids


def build_similarity_index(
    index: dict[str, dict],
    dataset: dict[str, dict],
    provider: ps.BaseContentProvider,
    label: str,
) -> dict[str, dict]:
    """Per-instance patch-similarity metrics keyed by instance_id.

    Each value holds the instance-level average of every metric in
    ``SIMILARITY_METRICS`` (averaged over the instance's commented files /
    functions). Instances whose repo is unavailable are omitted.
    """
    similarity: dict[str, dict] = {}
    for instance_id, result in index.items():
        instance = dataset.get(instance_id)
        if instance is None:
            continue
        file_rows, function_rows, repo_available = ps.compute_instance_rows(
            instance_id, instance, result, label, provider
        )
        if not repo_available:
            continue
        rows_by_level = {"file": file_rows, "function": function_rows}
        metrics: dict[str, float | None] = {}
        for metric_key, row_key, level in SIMILARITY_METRICS:
            values = [row[row_key] for row in rows_by_level[level]]
            metrics[metric_key] = safe_average(sum(values), len(values))
        similarity[instance_id] = metrics
    return similarity


# Over-edit metrics: per-instance line counts of how much the agent changed
# beyond the human gt patch (see patch_similarity.compute_over_edit).
OVER_EDIT_METRICS = (
    ("gt_edit_lines", "Avg gt edit lines (commented)"),
    ("agent_edit_lines", "Avg agent edit lines (commented)"),
    ("over_edited_lines", "Avg over-edited lines (commented)"),
    ("extra_file_lines", "Avg edited lines in non-commented files"),
    ("extra_files", "Avg non-commented files edited"),
)


def build_over_edit_index(
    index: dict[str, dict],
    dataset: dict[str, dict],
    provider: ps.BaseContentProvider,
) -> dict[str, dict]:
    """Per-instance over-edit line counts keyed by instance_id.

    Instances whose repo is unavailable are omitted.
    """
    over_edit: dict[str, dict] = {}
    for instance_id, result in index.items():
        instance = dataset.get(instance_id)
        if instance is None:
            continue
        counts = ps.compute_over_edit(instance, result, provider)
        if counts is None:
            continue
        over_edit[instance_id] = counts
    return over_edit


def average_over_edit(
    instance_ids: list[str],
    over_edit_index: dict[str, dict],
    metric_key: str,
) -> float | None:
    total = 0.0
    count = 0
    for instance_id in instance_ids:
        counts = over_edit_index.get(instance_id)
        if counts is None:
            continue
        total += counts.get(metric_key, 0)
        count += 1
    return safe_average(total, count)


def pooled_over_edit_rate(
    instance_ids: list[str],
    over_edit_index: dict[str, dict],
    numerator_key: str,
    denominator_key: str,
) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for instance_id in instance_ids:
        counts = over_edit_index.get(instance_id)
        if counts is None:
            continue
        numerator += counts.get(numerator_key, 0)
        denominator += counts.get(denominator_key, 0)
    return numerator / denominator if denominator else None


def over_edit_summary_rows(
    instance_ids_per_label: list[list[str]],
    over_edit_indexes: list[dict[str, dict]] | None,
    labels: list[str],
) -> list[tuple[str, ...]]:
    """One row per over-edit metric, averaged per label, plus a pooled rate."""
    if not over_edit_indexes:
        return []
    rows: list[tuple[str, ...]] = []
    for metric_key, title in OVER_EDIT_METRICS:
        rows.append(
            (
                title,
                *(
                    format_average(average_over_edit(instance_ids, over_edit_index, metric_key))
                    for instance_ids, over_edit_index in zip(
                        instance_ids_per_label, over_edit_indexes, strict=True
                    )
                ),
            )
        )
    def rate_cell(instance_ids: list[str], over_edit_index: dict[str, dict]) -> str:
        rate = pooled_over_edit_rate(
            instance_ids, over_edit_index, "over_edited_lines", "agent_edit_lines"
        )
        return MISSING if rate is None else f"{rate:.1%}"

    rows.append(
        (
            "Over-edit rate (over/agent, commented)",
            *(
                rate_cell(instance_ids, over_edit_index)
                for instance_ids, over_edit_index in zip(
                    instance_ids_per_label, over_edit_indexes, strict=True
                )
            ),
        )
    )
    return rows


def average_similarity_metric(
    instance_ids: list[str],
    similarity_index: dict[str, dict],
    metric_key: str,
) -> float | None:
    total = 0.0
    count = 0
    for instance_id in instance_ids:
        metrics = similarity_index.get(instance_id)
        value = metrics.get(metric_key) if metrics else None
        if value is None:
            continue
        total += value
        count += 1
    return safe_average(total, count)


def safe_filename_label(label: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in label)


def write_missing_instance_files(
    dataset_instance_ids: list[str],
    indexes: list[dict[str, dict]],
    labels: list[str],
    output_dir: Path,
) -> list[tuple[str, int, Path]]:
    """Write missing dataset instance IDs for each method label."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int, Path]] = []
    for label, index in zip(labels, indexes, strict=True):
        missing_ids = [instance_id for instance_id in dataset_instance_ids if instance_id not in index]
        output_file = output_dir / f"missing_instances_{safe_filename_label(label)}.txt"
        output_file.write_text(
            "".join(f"{instance_id}\n" for instance_id in missing_ids),
            encoding="utf-8",
        )
        written.append((label, len(missing_ids), output_file))

    return written


def safe_rate(passed: int, tests: int) -> float:
    return passed / tests if tests else 0.0


def safe_average(total: float, count: int) -> float | None:
    return total / count if count else None


def format_average(value: float | None, digits: int = 1) -> str:
    return MISSING if value is None else f"{value:.{digits}f}"


def get_numeric_stat(stats: dict | None, keys: tuple[str, ...]) -> float | None:
    if stats is None:
        return None

    return get_numeric_value(stats, keys)


def average_stat(
    instance_ids: list[str],
    stats_index: dict[str, dict],
    keys: tuple[str, ...],
) -> float | None:
    total = 0.0
    count = 0
    for instance_id in instance_ids:
        value = get_numeric_stat(stats_index.get(instance_id), keys)
        if value is None:
            continue
        total += value
        count += 1

    return safe_average(total, count)


def average_uncached_input_tokens(
    instance_ids: list[str],
    stats_index: dict[str, dict],
) -> float | None:
    total = 0.0
    count = 0
    for instance_id in instance_ids:
        stats = stats_index.get(instance_id)
        input_tokens = get_numeric_stat(stats, INPUT_TOKEN_KEYS)
        if input_tokens is None:
            continue

        cache_read_input_tokens = get_numeric_stat(stats, CACHE_READ_INPUT_TOKEN_KEYS) or 0.0
        total += input_tokens - cache_read_input_tokens
        count += 1

    return safe_average(total, count)


def calculate_token_cost(stats: dict | None, model: str = DEFAULT_PRICE_MODEL) -> float | None:
    if stats is None:
        return None

    prices = PRICES.get(model, PRICES[DEFAULT_PRICE_MODEL])
    input_tokens = get_numeric_stat(stats, INPUT_TOKEN_KEYS)
    output_tokens = get_numeric_stat(stats, OUTPUT_TOKEN_KEYS)
    cache_read_input_tokens = get_numeric_stat(stats, CACHE_READ_INPUT_TOKEN_KEYS) or 0.0
    cache_creation_input_tokens = get_numeric_stat(stats, CACHE_CREATION_INPUT_TOKEN_KEYS) or 0.0

    if input_tokens is None and output_tokens is None and cache_read_input_tokens == 0.0 and cache_creation_input_tokens == 0.0:
        return None

    # The harness reports input_tokens as the TOTAL prompt (cached + uncached),
    # with cache hits/writes broken out separately, so subtract them back out.
    uncached_input_tokens = max((input_tokens or 0.0) - cache_read_input_tokens - cache_creation_input_tokens, 0.0)
    return (
        uncached_input_tokens * prices["input"]
        + (output_tokens or 0.0) * prices["output"]
        + cache_creation_input_tokens * prices["cache_creation"]
        + cache_read_input_tokens * prices["cache_read"]
    ) / 1_000_000


def average_token_cost(
    instance_ids: list[str],
    stats_index: dict[str, dict],
    model: str = DEFAULT_PRICE_MODEL,
) -> float | None:
    total = 0.0
    count = 0
    for instance_id in instance_ids:
        cost = calculate_token_cost(stats_index.get(instance_id), model)
        if cost is None:
            continue
        total += cost
        count += 1

    return safe_average(total, count)


def get_field(result: dict | None, key: str, default):
    if result is None:
        return default
    return result.get(key, default)


def get_groundtruth_tests(result: dict | None) -> dict[str, dict]:
    """Return groundtruth assessment tests keyed by comment_index."""
    if result is None:
        return {}

    tests: dict[str, dict] = {}
    assessment = result.get("groundtruth_assessment") or {}

    for offset, item in enumerate(assessment.get("results", [])):
        if not isinstance(item, dict):
            continue

        comment_index = item.get("comment_index", offset)
        tests[str(comment_index)] = {
            "comment_index": comment_index,
            "comment_text": item.get("comment_text", ""),
            "test_file": item.get("test_filename", ""),
            "passed": item.get("passed"),
            "error": item.get("error", ""),
        }

    return tests


def get_replay_tests(result: dict | None) -> dict[str, dict]:
    """Return replay tests keyed by comment_index."""
    if result is None:
        return {}

    tests: dict[str, dict] = {}
    for offset, item in enumerate(result.get("results", [])):
        if not isinstance(item, dict):
            continue

        comment_index = item.get("comment_index", offset)
        tests[str(comment_index)] = {
            "comment_index": comment_index,
            "comment_text": item.get("comment_text", ""),
            "test_file": item.get("test_file", ""),
            "passed": item.get("test_passed"),
            "error": item.get("error", ""),
        }

    return tests


def get_tests(result: dict | None) -> dict[str, dict]:
    """Return tests using the format advertised by the result payload."""
    if result is None:
        return {}
    if "groundtruth_assessment" in result:
        return get_groundtruth_tests(result)
    return get_replay_tests(result)


def count_tests(tests: dict[str, dict]) -> int:
    return len(tests)


def count_passed(tests: dict[str, dict]) -> int:
    return sum(1 for item in tests.values() if item.get("passed") is True)


def load_comment_intent_gt(path: Path) -> dict[tuple[str, str], str]:
    """Load groundtruth comment-intent labels keyed by (instance_id, comment_index)."""
    gt: dict[tuple[str, str], str] = {}
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: Could not read comment intent GT file {path}: {exc}")
        return gt

    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: Could not parse {path}:{line_number}: {exc}")
                continue

            instance_id = data.get("instance_id")
            comment_index = data.get("comment_index")
            label = data.get("label")
            if instance_id is None or comment_index is None or label is None:
                continue
            gt[(str(instance_id), str(comment_index))] = label

    return gt


def pass_counts_by_comment_type(
    instance_ids: list[str],
    index: dict[str, dict],
    gt: dict[tuple[str, str], str],
) -> dict[str, list[int]]:
    """Per comment-type [passed, total] over the given instances of one method."""
    counts: dict[str, list[int]] = {}
    for instance_id in instance_ids:
        for comment_index, item in get_tests(index.get(instance_id)).items():
            comment_type = gt.get((str(instance_id), str(comment_index)))
            if comment_type is None:
                continue
            bucket = counts.setdefault(comment_type, [0, 0])
            bucket[1] += 1
            if item.get("passed") is True:
                bucket[0] += 1
    return counts


def comment_type_summary_rows(
    instance_ids_per_label: list[list[str]],
    indexes: list[dict[str, dict]],
    labels: list[str],
    gt: dict[tuple[str, str], str],
) -> list[tuple[str, ...]]:
    """One pass-rate row per comment type, with a count breakdown per label."""
    if not gt:
        return []
    counts_per_label = [
        pass_counts_by_comment_type(instance_ids, index, gt)
        for instance_ids, index in zip(instance_ids_per_label, indexes, strict=True)
    ]
    rows: list[tuple[str, ...]] = []
    for comment_type in COMMENT_TYPES:
        if not any(counts.get(comment_type, [0, 0])[1] for counts in counts_per_label):
            continue
        cells = []
        for counts in counts_per_label:
            passed, total = counts.get(comment_type, [0, 0])
            cells.append(f"{safe_rate(passed, total):.1%} ({passed}/{total})" if total else MISSING)
        rows.append((f"Pass rate ({comment_type})", *cells))
    return rows


def load_assertion_counts(root: Path) -> dict[tuple[str, str], int]:
    """Load groundtruth per-comment assertion counts keyed by (instance_id, comment_index)."""
    counts: dict[tuple[str, str], int] = {}
    for result_file in sorted(root.rglob("result.json")):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: Could not read {result_file}: {exc}")
            continue

        instance_id = data.get("instance_id") or result_file.parent.name
        for item in data.get("results", []):
            if not isinstance(item, dict):
                continue
            num_assertions = item.get("num_assertions")
            # A comment whose GT validation test was invalid has no parsed assertion
            # count (num_assertions=None, total_assertions=0). Treat it as 0 so it is
            # still bucketed (into "0-1 asserts") instead of dropped from the table.
            if num_assertions is None:
                num_assertions = 0
            counts[(str(instance_id), str(item.get("comment_index")))] = int(num_assertions)
    return counts


def assertion_bucket_of(num_assertions: int) -> str | None:
    for label, predicate in ASSERTION_BUCKETS:
        if predicate(num_assertions):
            return label
    return None


def pass_counts_by_assertion_bucket(
    instance_ids: list[str],
    index: dict[str, dict],
    assertion_counts: dict[tuple[str, str], int],
) -> dict[str, list[int]]:
    """Per assertion-count bucket [passed, total] over the given instances of one method."""
    counts: dict[str, list[int]] = {}
    for instance_id in instance_ids:
        for comment_index, item in get_tests(index.get(instance_id)).items():
            num_assertions = assertion_counts.get((str(instance_id), str(comment_index)))
            if num_assertions is None:
                continue
            bucket = assertion_bucket_of(num_assertions)
            if bucket is None:
                continue
            entry = counts.setdefault(bucket, [0, 0])
            entry[1] += 1
            if item.get("passed") is True:
                entry[0] += 1
    return counts


def assertion_bucket_summary_rows(
    instance_ids_per_label: list[list[str]],
    indexes: list[dict[str, dict]],
    labels: list[str],
    assertion_counts: dict[tuple[str, str], int],
) -> list[tuple[str, ...]]:
    """One pass-rate row per assertion-count bucket, with a count breakdown per label."""
    if not assertion_counts:
        return []
    counts_per_label = [
        pass_counts_by_assertion_bucket(instance_ids, index, assertion_counts)
        for instance_ids, index in zip(instance_ids_per_label, indexes, strict=True)
    ]
    rows: list[tuple[str, ...]] = []
    for bucket, _predicate in ASSERTION_BUCKETS:
        if not any(counts.get(bucket, [0, 0])[1] for counts in counts_per_label):
            continue
        cells = []
        for counts in counts_per_label:
            passed, total = counts.get(bucket, [0, 0])
            cells.append(f"{safe_rate(passed, total):.1%} ({passed}/{total})" if total else MISSING)
        rows.append((f"Pass rate ({bucket})", *cells))
    return rows


def load_difficulty_map(path: Path) -> dict[str, str]:
    """Load instance difficulty from dataset metadata, keyed by instance_id."""
    difficulty: dict[str, str] = {}
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: Could not read dataset file {path}: {exc}")
        return difficulty

    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: Could not parse {path}:{line_number}: {exc}")
                continue

            instance_id = data.get("instance_id")
            level = (data.get("metadata") or {}).get("difficulty")
            if instance_id is None or level is None:
                continue
            difficulty[str(instance_id)] = level

    return difficulty


def pass_counts_by_difficulty(
    instance_ids: list[str],
    index: dict[str, dict],
    difficulty_map: dict[str, str],
) -> dict[str, list[int]]:
    """Per difficulty level [passed, total] over the given instances of one method."""
    counts: dict[str, list[int]] = {}
    for instance_id in instance_ids:
        level = difficulty_map.get(str(instance_id))
        if level is None:
            continue
        for item in get_tests(index.get(instance_id)).values():
            entry = counts.setdefault(level, [0, 0])
            entry[1] += 1
            if item.get("passed") is True:
                entry[0] += 1
    return counts


def difficulty_summary_rows(
    instance_ids_per_label: list[list[str]],
    indexes: list[dict[str, dict]],
    labels: list[str],
    difficulty_map: dict[str, str],
) -> list[tuple[str, ...]]:
    """One pass-rate row per difficulty level, with a count breakdown per label."""
    if not difficulty_map:
        return []
    counts_per_label = [
        pass_counts_by_difficulty(instance_ids, index, difficulty_map)
        for instance_ids, index in zip(instance_ids_per_label, indexes, strict=True)
    ]
    rows: list[tuple[str, ...]] = []
    for level in DIFFICULTY_LEVELS:
        if not any(counts.get(level, [0, 0])[1] for counts in counts_per_label):
            continue
        cells = []
        for counts in counts_per_label:
            passed, total = counts.get(level, [0, 0])
            cells.append(f"{safe_rate(passed, total):.1%} ({passed}/{total})" if total else MISSING)
        rows.append((f"Pass rate ({level})", *cells))
    return rows


def build_row(
    instance_id: str,
    results: list[dict | None],
    labels: list[str],
    similarity_by_label: dict[str, dict[str, dict]],
    include_similarity: bool,
) -> dict:
    """Build one CSV row for a single instance."""
    tests_by_label = {
        label: get_tests(result)
        for label, result in zip(labels, results, strict=True)
    }
    repo = next((get_field(result, "repo", "") for result in results if result is not None), "")

    row = {
        "instance_id": instance_id,
        "repo": repo,
    }
    for label, result in zip(labels, results, strict=True):
        tests = tests_by_label[label]
        num_tests = count_tests(tests)
        num_passed = count_passed(tests)
        row.update(
            {
                f"{label}_present": int(result is not None),
                f"{label}_num_tests": num_tests if result is not None else MISSING,
                f"{label}_num_passed": num_passed if result is not None else MISSING,
                f"{label}_pass_rate": round(safe_rate(num_passed, num_tests), 4)
                if result is not None
                else MISSING,
                f"{label}_error": get_field(result, "error", "") if result is not None else MISSING,
            }
        )
        if include_similarity:
            metrics = similarity_by_label.get(label, {}).get(instance_id)
            for metric_key, *_ in SIMILARITY_METRICS:
                value = metrics.get(metric_key) if metrics else None
                row[f"{label}_{metric_key}"] = round(value, 4) if value is not None else MISSING
    return row


def count_unique_passed_for_label(
    instance_ids: list[str],
    tests_by_label: dict[str, dict[str, dict[str, dict]]],
    label: str,
) -> int:
    unique_count = 0
    other_labels = [other_label for other_label in tests_by_label if other_label != label]

    for instance_id in instance_ids:
        current_passed = {
            index
            for index, item in tests_by_label[label][instance_id].items()
            if item.get("passed") is True
        }
        other_passed = set()
        for other_label in other_labels:
            other_passed.update(
                index
                for index, item in tests_by_label[other_label][instance_id].items()
                if item.get("passed") is True
            )
        unique_count += len(current_passed - other_passed)

    return unique_count


SIMILARITY_DISPLAY_NAMES = {
    "file_bleu": "File BLEU (avg)",
    "file_edit_sim": "File edit-sim (avg)",
    "func_bleu": "Function BLEU (avg)",
    "func_edit_sim": "Function edit-sim (avg)",
}


def similarity_summary_rows(
    instance_ids_per_label: list[list[str]],
    similarity_indexes: list[dict[str, dict]],
    labels: list[str],
) -> list[tuple[str, ...]]:
    """Build one summary row per similarity metric, averaged per label."""
    rows: list[tuple[str, ...]] = []
    for metric_key, _row_key, _level in SIMILARITY_METRICS:
        rows.append(
            (
                SIMILARITY_DISPLAY_NAMES[metric_key],
                *(
                    format_average(
                        average_similarity_metric(instance_ids, similarity_index, metric_key),
                        digits=4,
                    )
                    for instance_ids, similarity_index in zip(
                        instance_ids_per_label, similarity_indexes, strict=True
                    )
                ),
            )
        )
    return rows


def summarize_overlap(
    overlap_ids: list[str],
    indexes: list[dict[str, dict]],
    stats_indexes: list[dict[str, dict]],
    similarity_indexes: list[dict[str, dict]] | None,
    labels: list[str],
    models: list[str],
) -> list[tuple[str, ...]]:
    """Return rows for a comparison table with one column per result folder."""
    tests_by_label = {
        label: {iid: get_tests(index[iid]) for iid in overlap_ids}
        for label, index in zip(labels, indexes, strict=True)
    }
    totals_by_label = {}
    for label, index in zip(labels, indexes, strict=True):
        tests_by_id = tests_by_label[label]
        total_tests = sum(count_tests(tests) for tests in tests_by_id.values())
        total_passed = sum(count_passed(tests) for tests in tests_by_id.values())
        totals_by_label[label] = {
            "available": len(index),
            "overlap": len(overlap_ids),
            "tests": total_tests,
            "passed": total_passed,
            "rate": safe_rate(total_passed, total_tests),
            "any_passed": sum(1 for tests in tests_by_id.values() if count_passed(tests) > 0),
            "unique_passed": count_unique_passed_for_label(overlap_ids, tests_by_label, label),
        }

    baseline_rate = totals_by_label[labels[0]]["rate"] if labels else 0.0

    return [
        ("Instances available", *(str(totals_by_label[label]["available"]) for label in labels)),
        ("Instances in overlap", *(str(totals_by_label[label]["overlap"]) for label in labels)),
        ("Total tests (overlap)", *(str(totals_by_label[label]["tests"]) for label in labels)),
        ("Total passed (overlap)", *(str(totals_by_label[label]["passed"]) for label in labels)),
        (
            "Pass rate (overlap)",
            *(f"{totals_by_label[label]['rate']:.1%}" for label in labels),
        ),
        ("Instances with any passed", *(str(totals_by_label[label]["any_passed"]) for label in labels)),
        ("Unique passed comments", *(str(totals_by_label[label]["unique_passed"]) for label in labels)),
        (
            f"Pass rate gap vs {labels[0]}",
            *(f"{totals_by_label[label]['rate'] - baseline_rate:.1%}" for label in labels),
        ),
        (
            "Avg input token",
            *(
                format_average(average_uncached_input_tokens(overlap_ids, stats_index))
                for stats_index in stats_indexes
            ),
        ),
        (
            "Avg output token",
            *(
                format_average(average_stat(overlap_ids, stats_index, OUTPUT_TOKEN_KEYS))
                for stats_index in stats_indexes
            ),
        ),
        (
            "Avg cache read input token",
            *(
                format_average(average_stat(overlap_ids, stats_index, CACHE_READ_INPUT_TOKEN_KEYS))
                for stats_index in stats_indexes
            ),
        ),
        ("Pricing model", *models),
        (
            "Avg cost",
            *(
                format_average(average_token_cost(overlap_ids, stats_index, model), digits=4)
                for stats_index, model in zip(stats_indexes, models, strict=True)
            ),
        ),
        *(
            similarity_summary_rows([overlap_ids for _ in labels], similarity_indexes, labels)
            if similarity_indexes is not None
            else []
        ),
    ]


def summarize_all_results(
    indexes: list[dict[str, dict]],
    stats_indexes: list[dict[str, dict]],
    similarity_indexes: list[dict[str, dict]] | None,
    labels: list[str],
    models: list[str],
) -> list[tuple[str, ...]]:
    """Return summary rows where each folder is evaluated on all of its own results."""
    totals_by_label = {}
    for label, index in zip(labels, indexes, strict=True):
        tests_by_id = {iid: get_tests(result) for iid, result in index.items()}
        total_tests = sum(count_tests(tests) for tests in tests_by_id.values())
        total_passed = sum(count_passed(tests) for tests in tests_by_id.values())
        totals_by_label[label] = {
            "available": len(index),
            "tests": total_tests,
            "passed": total_passed,
            "rate": safe_rate(total_passed, total_tests),
            "any_passed": sum(1 for tests in tests_by_id.values() if count_passed(tests) > 0),
        }

    baseline_rate = totals_by_label[labels[0]]["rate"] if labels else 0.0

    return [
        ("Instances available", *(str(totals_by_label[label]["available"]) for label in labels)),
        ("Total tests", *(str(totals_by_label[label]["tests"]) for label in labels)),
        ("Total passed", *(str(totals_by_label[label]["passed"]) for label in labels)),
        (
            "Pass rate",
            *(f"{totals_by_label[label]['rate']:.1%}" for label in labels),
        ),
        ("Instances with any passed", *(str(totals_by_label[label]["any_passed"]) for label in labels)),
        (
            f"Pass rate gap vs {labels[0]}",
            *(f"{totals_by_label[label]['rate'] - baseline_rate:.1%}" for label in labels),
        ),
        (
            "Avg input token",
            *(
                format_average(average_uncached_input_tokens(list(index), stats_index))
                for index, stats_index in zip(indexes, stats_indexes, strict=True)
            ),
        ),
        (
            "Avg output token",
            *(
                format_average(average_stat(list(index), stats_index, OUTPUT_TOKEN_KEYS))
                for index, stats_index in zip(indexes, stats_indexes, strict=True)
            ),
        ),
        (
            "Avg cache read input token",
            *(
                format_average(average_stat(list(index), stats_index, CACHE_READ_INPUT_TOKEN_KEYS))
                for index, stats_index in zip(indexes, stats_indexes, strict=True)
            ),
        ),
        ("Pricing model", *models),
        (
            "Avg cost",
            *(
                format_average(average_token_cost(list(index), stats_index, model), digits=4)
                for index, stats_index, model in zip(indexes, stats_indexes, models, strict=True)
            ),
        ),
        *(
            similarity_summary_rows([list(index) for index in indexes], similarity_indexes, labels)
            if similarity_indexes is not None
            else []
        ),
    ]


def full_pass_keys_by_label(
    indexes: list[dict[str, dict]], labels: list[str]
) -> dict[str, set[tuple]]:
    """(instance_id, comment_index) pairs that PASSED the full (unsplit) test, per
    label. Uses get_tests() -- i.e. groundtruth_assessment when present, else the
    folder's results[].test_passed -- the same pass signal as the table's top
    'Total passed' section."""
    out: dict[str, set[tuple]] = {}
    for label, index in zip(labels, indexes, strict=True):
        keys: set[tuple] = set()
        for iid, result in index.items():
            for test in get_tests(result).values():
                if test.get("passed") is True:
                    keys.add((iid, test.get("comment_index")))
        out[label] = keys
    return out


def compute_split_eval_metrics(
    labels: list[str], root: Path, full_pass: dict[str, set[tuple]] | None = None
) -> dict:
    """Per-label patch-verification metrics from report_eval_on_split.

    Reuses report_eval_on_split's loaders so the numbers match
    ``python report_eval_on_split.py`` exactly. Returns a dict keyed by label
    plus a ``"_totals"`` entry with the fixed assertion/F2P/P2P denominators.
    Returns {} when report_eval_on_split is unavailable.

    ``full_pass`` maps each label to the set of (instance_id, comment_index) that
    passed the full (unsplit) test. For those comments every split sub-test is
    counted as passed, overriding the raw split-eval result -- this absorbs
    spurious split-eval failures (patch failed to re-apply, collection errors)
    for comments that genuinely passed. When None/empty the raw split results are
    used unchanged.
    """
    if rep is None:
        print("WARNING: report_eval_on_split not importable; split-eval metrics omitted.")
        return {}

    full_pass = full_pass or {}
    fixed = rep.fixed_counts()
    fixed_total = sum(fixed.values())
    names = rep.canonical_names()
    all_keys = {(iid, cidx, nm) for (iid, cidx), nms in names.items() for nm in nms}
    p2p = rep.p2p_keys(names) & all_keys
    f2p = all_keys - p2p
    f2p_total, p2p_total = len(f2p), len(p2p)

    out: dict = {"_totals": {"asserts": fixed_total, "F2P_tot": f2p_total, "P2P_tot": p2p_total}}
    for label in labels:
        folder = SPLIT_EVAL_FOLDERS.get(label)
        if folder is None:
            continue
        sub = root / folder
        if not (sub / "summary.json").exists():
            print(f"WARNING: no summary.json for split-eval label '{label}' under {sub}")
            continue
        summ, per_comment, fully, applied = rep.load_agent(sub)
        fp = full_pass.get(label, set())
        apass = c100 = 0
        for key, fixed_n in fixed.items():
            # Full-test pass -> all of this comment's split sub-tests count as passed.
            passed = fixed_n if key in fp else min(per_comment.get(key, (0, 0))[1], fixed_n)
            apass += passed
            if fixed_n and passed / fixed_n >= 1.0:
                c100 += 1
        passed_keys = set(rep.agent_passed_keys(sub))
        for key in fp:
            for nm in names.get(key, []):
                passed_keys.add((key[0], key[1], nm))
        f2p_pass = len(passed_keys & f2p)
        p2p_keep = len(passed_keys & p2p)
        out[label] = {
            "tPass": c100,
            "aPass": apass,
            "aRate": apass / fixed_total if fixed_total else 0.0,
            "fullyOK": fully,
            "applied": applied,
            "err": summ.get("total_errors", 0) if summ else 0,
            "F2P_pass": f2p_pass,
            "F2P_rate": f2p_pass / f2p_total if f2p_total else 0.0,
            "P2P_keep": p2p_keep,
            "P2P_brk": p2p_total - p2p_keep,
        }
    return out


def split_eval_summary_rows(labels: list[str], split_metrics: dict) -> list[tuple[str, ...]]:
    """Build comparison rows (one per split-eval metric) for the summary table."""
    if not split_metrics:
        return []
    totals = split_metrics.get("_totals", {})

    def cell(label: str, key: str, pct: bool = False) -> str:
        metrics = split_metrics.get(label)
        if not metrics or key not in metrics:
            return MISSING
        value = metrics[key]
        return f"{value:.1%}" if pct else str(value)

    asserts = totals.get("asserts", "?")
    f2p_tot = totals.get("F2P_tot", "?")
    p2p_tot = totals.get("P2P_tot", "?")
    specs: list[tuple[str, str, bool]] = [
        ("Split tPass (c=100%)", "tPass", False),
        (f"Split aPass (/{asserts})", "aPass", False),
        ("Split aRate", "aRate", True),
        ("Split fullyOK", "fullyOK", False),
        ("Split patch applied", "applied", False),
        ("Split errors", "err", False),
        (f"Split F2P pass (/{f2p_tot})", "F2P_pass", False),
        ("Split F2P rate", "F2P_rate", True),
        (f"Split P2P keep (/{p2p_tot})", "P2P_keep", False),
        ("Split P2P broken", "P2P_brk", False),
    ]
    return [(title, *(cell(label, key, pct) for label in labels)) for title, key, pct in specs]


def format_table(headers: list[str], rows: list[tuple[str, ...]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt(row: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    parts = [fmt(tuple(headers)), separator]
    parts.extend(fmt(row) for row in rows)
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare result folders with automatically detected test result formats."
    )
    parser.add_argument(
        "result_dirs",
        nargs="*",
        type=Path,
        default=DEFAULT_RESULT_DIRS,
        help=f"Result directories to compare (default: {' '.join(str(path) for path in DEFAULT_RESULT_DIRS)})",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        help="Short labels for result directories in CSV/table output",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_CSV})",
    )
    parser.add_argument(
        "--dataset-file",
        type=Path,
        default=DATASET_FILE,
        help=f"Dataset JSONL used to find missing instances (default: {DATASET_FILE})",
    )
    parser.add_argument(
        "--missing-instances-dir",
        type=Path,
        default=DEFAULT_MISSING_INSTANCES_DIR,
        help=f"Directory for missing instance ID lists (default: {DEFAULT_MISSING_INSTANCES_DIR})",
    )
    parser.add_argument(
        "--repos-dir",
        type=Path,
        default=DEFAULT_REPOS_DIR,
        help=f"Local git checkouts used for patch-similarity metrics (default: {DEFAULT_REPOS_DIR})",
    )
    parser.add_argument(
        "--similarity",
        action="store_true",
        help="Compute patch-similarity metrics (BLEU / edit similarity); off by default",
    )
    parser.add_argument(
        "--split-eval-root",
        type=Path,
        default=SPLIT_EVAL_ROOT,
        help=f"Patch-verification results root for split-eval metrics (default: {SPLIT_EVAL_ROOT})",
    )
    parser.add_argument(
        "--no-split-eval",
        action="store_true",
        help="Skip the report_eval_on_split.py patch-verification metric rows",
    )
    parser.add_argument(
        "--no-fulltest-override",
        action="store_true",
        help="Disable the rule that a comment passing its full (unsplit) test marks "
        "all of its split sub-tests as passed (use raw split-eval results instead)",
    )
    args = parser.parse_args()

    result_dirs = args.result_dirs
    if args.labels:
        labels = args.labels
    elif result_dirs == DEFAULT_RESULT_DIRS:
        labels = SHORT_LABELS
    else:
        labels = [path.name for path in result_dirs]

    if len(result_dirs) < 2:
        parser.error("Provide at least two result directories to compare.")
    if len(labels) != len(result_dirs):
        parser.error(f"Expected {len(result_dirs)} labels, got {len(labels)}.")
    if len(set(labels)) != len(labels):
        parser.error("Labels must be unique.")

    output_csv = args.output_csv or result_dirs[0] / "compare.csv"
    # Per-method pricing model (defaults to qwen-plus for any label not mapped).
    models = [AGENT_MODEL.get(label, DEFAULT_PRICE_MODEL) for label in labels]

    indexes = []
    for result_dir, label in zip(result_dirs, labels, strict=True):
        index = load_result_index(result_dir)
        print(f"[load results ] {label}: {len(index)} instances loaded", flush=True)
        indexes.append(index)

    stats_indexes = []
    for result_dir, label in zip(result_dirs, labels, strict=True):
        stats_index = load_stats_index(result_dir)
        print(f"[load stats   ] {label}: {len(stats_index)} trajectory stats loaded", flush=True)
        stats_indexes.append(stats_index)

    # Fold each method's intent-classification + test-generation token usage into
    # its agent stats so the token/cost columns cover the whole pipeline.
    merge_stage_stats(stats_indexes, labels)
    similarity_indexes = None
    similarity_by_label: dict[str, dict[str, dict]] = {}
    over_edit_indexes: list[dict[str, dict]] | None = None
    if args.similarity:
        if ps is None:
            parser.error("--similarity requires patch_similarity and its dependencies (e.g. Levenshtein).")
        dataset_instances = ps.load_dataset(args.dataset_file)
        similarity_provider = ps.BaseContentProvider(args.repos_dir)
        similarity_indexes = []
        over_edit_indexes = []
        for index, label in zip(indexes, labels, strict=True):
            sim_index = build_similarity_index(index, dataset_instances, similarity_provider, label)
            print(f"[similarity   ] {label}: computed for {len(sim_index)} instances", flush=True)
            similarity_indexes.append(sim_index)
            over_edit_index = build_over_edit_index(index, dataset_instances, similarity_provider)
            print(f"[over-edit    ] {label}: computed for {len(over_edit_index)} instances", flush=True)
            over_edit_indexes.append(over_edit_index)
        similarity_by_label = dict(zip(labels, similarity_indexes, strict=True))
        if similarity_provider.missing_repos:
            print(
                f"WARNING: {len(similarity_provider.missing_repos)} repos not found under {args.repos_dir}; "
                f"patch-similarity metrics omitted for instances using them."
            )
    dataset_instance_ids = load_dataset_instance_ids(args.dataset_file)
    missing_instance_files = write_missing_instance_files(
        dataset_instance_ids=dataset_instance_ids,
        indexes=indexes,
        labels=labels,
        output_dir=args.missing_instances_dir,
    )

    all_ids = sorted(set().union(*(set(index) for index in indexes)))
    overlap_ids = sorted(set.intersection(*(set(index) for index in indexes)))

    rows = [
        build_row(
            instance_id=iid,
            results=[index.get(iid) for index in indexes],
            labels=labels,
            similarity_by_label=similarity_by_label,
            include_similarity=args.similarity,
        )
        for iid in all_ids
    ]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "instance_id",
        "repo",
        *(f"{label}_present" for label in labels),
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("[split eval   ] computing patch-verification metrics...", flush=True)
    full_pass = {} if args.no_fulltest_override else full_pass_keys_by_label(indexes, labels)
    if full_pass:
        print(
            "[split eval   ] full-test override ON: "
            + ", ".join(f"{lab}={len(keys)}" for lab, keys in full_pass.items()),
            flush=True,
        )
    split_metrics = (
        {} if args.no_split_eval else compute_split_eval_metrics(labels, args.split_eval_root, full_pass)
    )
    print(f"[split eval   ] done ({len(split_metrics) - (1 if '_totals' in split_metrics else 0)} labels)", flush=True)
    split_rows = split_eval_summary_rows(labels, split_metrics)

    comment_intent_gt = load_comment_intent_gt(COMMENT_INTENT_GT_FILE)
    print(f"[comment type ] loaded {len(comment_intent_gt)} groundtruth labels", flush=True)
    all_comment_type_rows = comment_type_summary_rows(
        [list(index) for index in indexes], indexes, labels, comment_intent_gt
    )
    overlap_comment_type_rows = comment_type_summary_rows(
        [overlap_ids for _ in labels], indexes, labels, comment_intent_gt
    )

    assertion_counts = load_assertion_counts(GT_ASSERTION_DIR)
    print(f"[assertions   ] loaded {len(assertion_counts)} groundtruth assertion counts", flush=True)
    all_assertion_rows = assertion_bucket_summary_rows(
        [list(index) for index in indexes], indexes, labels, assertion_counts
    )
    overlap_assertion_rows = assertion_bucket_summary_rows(
        [overlap_ids for _ in labels], indexes, labels, assertion_counts
    )

    difficulty_map = load_difficulty_map(args.dataset_file)
    print(f"[difficulty   ] loaded {len(difficulty_map)} instance difficulties", flush=True)
    all_difficulty_rows = difficulty_summary_rows(
        [list(index) for index in indexes], indexes, labels, difficulty_map
    )
    overlap_difficulty_rows = difficulty_summary_rows(
        [overlap_ids for _ in labels], indexes, labels, difficulty_map
    )

    all_over_edit_rows = over_edit_summary_rows(
        [list(index) for index in indexes], over_edit_indexes, labels
    )
    overlap_over_edit_rows = over_edit_summary_rows(
        [overlap_ids for _ in labels], over_edit_indexes, labels
    )

    all_summary_rows = summarize_all_results(
        indexes=indexes,
        stats_indexes=stats_indexes,
        similarity_indexes=similarity_indexes,
        labels=labels,
        models=models,
    ) + split_rows + all_comment_type_rows + all_assertion_rows + all_difficulty_rows + all_over_edit_rows
    all_table = format_table(
        headers=["Metric", *labels],
        rows=all_summary_rows,
    )

    overlap_summary_rows = summarize_overlap(
        overlap_ids=overlap_ids,
        indexes=indexes,
        stats_indexes=stats_indexes,
        similarity_indexes=similarity_indexes,
        labels=labels,
        models=models,
    ) + split_rows + overlap_comment_type_rows + overlap_assertion_rows + overlap_difficulty_rows + overlap_over_edit_rows
    overlap_table = format_table(
        headers=["Metric", *labels],
        rows=overlap_summary_rows,
    )

    print(f"Wrote {len(rows)} instance rows to {output_csv}")
    print(f"Wrote missing instance lists to {args.missing_instances_dir}")
    for label, missing_count, output_file in missing_instance_files:
        print(f"  {label}: {missing_count} missing -> {output_file}")
    print()
    print("Whole results")
    print(all_table)
    print()
    print("Overlap results")
    print(overlap_table)
    
    # export summary tables to CSV files
    summary_output_dir = output_csv.parent / "summaries"
    summary_output_dir.mkdir(parents=True, exist_ok=True)
    all_summary_csv = summary_output_dir / "summary_all.csv"
    overlap_summary_csv = summary_output_dir / "summary_overlap.csv"
    with all_summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Metric", *labels])
        writer.writerows(all_summary_rows)
        
    with overlap_summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Metric", *labels])
        writer.writerows(overlap_summary_rows)


if __name__ == "__main__":
    main()
