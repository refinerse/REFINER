#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _usage_value(usage: dict[str, Any], key: str) -> float:
    value = usage.get(key, 0)
    return value if isinstance(value, (int, float)) else 0


def _true_count(series: pd.Series) -> int:
    return int(series.eq(True).sum())


def _run_index_from_path(path: Path) -> int | None:
    """Extract run index from filename like result_run_2.json -> 2."""
    m = re.search(r"result_run_(\d+)\.json$", path.name)
    return int(m.group(1)) if m else None


def summarize_comment_result(
    instance_id: str,
    repo: str | None,
    model: str | None,
    agent: str | None,
    run_index: int | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    assessment = result.get("assessment") or {}
    usage = result.get("usage") or {}

    # run_index may also be embedded in the result itself
    ri = result.get("run_index")
    if ri is None:
        ri = run_index

    return {
        "instance_id": instance_id,
        "repo": repo,
        "model": model,
        "agent": agent,
        "run_index": ri,
        "comment_index": result.get("comment_index"),
        "comment_text": result.get("comment_text"),
        "comment_type": result.get("comment_type"),
        "language": result.get("language"),
        "attempts_used": result.get("attempts_used"),
        "generation_succeeded": bool(result.get("test_code")),
        "expected_failure_observed": result.get("expected_failure_observed"),
        "success": result.get("success"),
        "current_passed": result.get("current_passed"),
        "ground_truth_patch_passed": assessment.get("ground_truth_patch_passed"),
        "groundtruth_correct": assessment.get("current_fails_and_patch_passes"),
        "error": result.get("error"),
        "test_file": result.get("test_file"),
        "prompt_tokens": int(_usage_value(usage, "prompt_tokens")),
        "completion_tokens": int(_usage_value(usage, "completion_tokens")),
        "total_tokens": int(_usage_value(usage, "total_tokens")),
        "cost_usd": float(_usage_value(usage, "cost_usd")),
    }


def summarize_instance_dir(instance_dir: Path) -> list[dict[str, Any]]:
    """Load all result_run_N.json files from an instance directory."""
    run_files = sorted(
        instance_dir.glob("result_run_*.json"),
        key=lambda p: (_run_index_from_path(p) or 0),
    )

    if not run_files:
        # Fall back to result.json if no per-run files found
        result_path = instance_dir / "result.json"
        if result_path.exists():
            run_files = [result_path]

    rows: list[dict[str, Any]] = []
    for run_file in run_files:
        run_index = _run_index_from_path(run_file)
        data = json.loads(run_file.read_text())

        # Support both a top-level list and a dict with a "results" key
        if isinstance(data, list):
            results = data
            repo = None
            model = None
            agent = None
        else:
            results = data.get("results") or []
            repo = data.get("repo")
            model = data.get("model")
            agent = data.get("agent")

        for result in results:
            rows.append(
                summarize_comment_result(
                    instance_id=instance_dir.name,
                    repo=repo,
                    model=model,
                    agent=agent,
                    run_index=run_index,
                    result=result,
                )
            )

    return rows


def build_run_df(results_dir: Path) -> pd.DataFrame:
    """One row per (instance, comment, run)."""
    rows: list[dict[str, Any]] = []
    for instance_dir in sorted(results_dir.iterdir()):
        if instance_dir.is_dir():
            rows.extend(summarize_instance_dir(instance_dir))

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values(["instance_id", "comment_index", "run_index"]).reset_index(
        drop=True
    )


def build_comment_df(run_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per (instance, comment) across all runs.

    Columns added:
      num_runs            – how many runs were recorded for this comment
      any_success         – True if ANY run succeeded (expected failure observed)
      all_success         – True if ALL runs succeeded
      any_groundtruth     – True if ANY run is ground-truth correct
      all_groundtruth     – True if ALL runs are ground-truth correct
      success_rate        – fraction of runs with success == True
      groundtruth_rate    – fraction of runs with groundtruth_correct == True
    """
    if run_df.empty:
        return pd.DataFrame()

    group_keys = ["instance_id", "comment_index"]

    agg = (
        run_df.groupby(group_keys, sort=True)
        .agg(
            repo=("repo", "first"),
            model=("model", "first"),
            agent=("agent", "first"),
            comment_text=("comment_text", "first"),
            comment_type=("comment_type", "first"),
            language=("language", "first"),
            num_runs=("run_index", "count"),
            any_generation_succeeded=("generation_succeeded", "any"),
            any_success=("success", lambda s: bool(s.eq(True).any())),
            all_success=("success", lambda s: bool(s.eq(True).all())),
            success_rate=(
                "success",
                lambda s: _safe_divide(int(s.eq(True).sum()), len(s)),
            ),
            any_groundtruth=("groundtruth_correct", lambda s: bool(s.eq(True).any())),
            all_groundtruth=(
                "groundtruth_correct",
                lambda s: bool(s.eq(True).all()),
            ),
            groundtruth_rate=(
                "groundtruth_correct",
                lambda s: _safe_divide(int(s.eq(True).sum()), len(s)),
            ),
            any_expected_failure=(
                "expected_failure_observed",
                lambda s: bool(s.eq(True).any()),
            ),
        )
        .reset_index()
    )

    return agg


def print_overall_summary(run_df: pd.DataFrame, comment_df: pd.DataFrame) -> None:
    num_instances = run_df["instance_id"].nunique()
    num_comments = len(comment_df)
    num_runs = len(run_df)
    runs_per_comment = run_df.groupby(["instance_id", "comment_index"]).size()

    print("=" * 60)
    print("Per-run statistics")
    print("=" * 60)
    gen_ok = _true_count(run_df["generation_succeeded"])
    exp_fail = _true_count(run_df["expected_failure_observed"])
    success = _true_count(run_df["success"])
    gt_correct = _true_count(run_df["groundtruth_correct"])
    print(f"  Instances:                  {num_instances}")
    print(f"  Unique comments:            {num_comments}")
    print(f"  Total runs (rows):          {num_runs}")
    print(f"  Avg runs per comment:       {runs_per_comment.mean():.2f}")
    print(f"  Generation succeeded:       {gen_ok} / {num_runs}  ({_safe_divide(gen_ok, num_runs):.2%})")
    print(f"  Expected failure observed:  {exp_fail} / {num_runs}  ({_safe_divide(exp_fail, num_runs):.2%})")
    print(f"  Success (expected failure): {success} / {num_runs}  ({_safe_divide(success, num_runs):.2%})")
    print(f"  Ground-truth correct:       {gt_correct} / {num_runs}  ({_safe_divide(gt_correct, num_runs):.2%})")

    print()
    print("=" * 60)
    print("Per-comment statistics (aggregated across runs)")
    print("=" * 60)
    any_success = _true_count(comment_df["any_success"])
    all_success = _true_count(comment_df["all_success"])
    any_gt = _true_count(comment_df["any_groundtruth"])
    all_gt = _true_count(comment_df["all_groundtruth"])
    print(f"  Unique comments:            {num_comments}")
    print(f"  Any-run success:            {any_success} / {num_comments}  ({_safe_divide(any_success, num_comments):.2%})")
    print(f"  All-runs success:           {all_success} / {num_comments}  ({_safe_divide(all_success, num_comments):.2%})")
    print(f"  Avg success rate:           {comment_df['success_rate'].mean():.2%}")
    print(f"  Any-run ground-truth corr.: {any_gt} / {num_comments}  ({_safe_divide(any_gt, num_comments):.2%})")
    print(f"  All-runs ground-truth corr.:{all_gt} / {num_comments}  ({_safe_divide(all_gt, num_comments):.2%})")
    print(f"  Avg ground-truth rate:      {comment_df['groundtruth_rate'].mean():.2%}")

    # pass@k estimate (unbiased, following Chen et al. 2021)
    k_values = [1, 2, 3]
    n_series = runs_per_comment
    c_series = (
        run_df[run_df["groundtruth_correct"].eq(True)]
        .groupby(["instance_id", "comment_index"])
        .size()
        .reindex(n_series.index, fill_value=0)
    )
    pass_at_k: dict[int, float] = {}
    for k in k_values:
        estimates = []
        for (iid, ci), n in n_series.items():
            c = c_series.get((iid, ci), 0)
            if n >= k:
                # 1 - C(n-c, k) / C(n, k)
                from math import comb
                val = 1.0 - comb(n - c, k) / comb(n, k) if n - c >= k else 1.0
                estimates.append(val)
        if estimates:
            pass_at_k[k] = sum(estimates) / len(estimates)

    if pass_at_k:
        print()
        print("  pass@k (ground-truth correctness, unbiased estimate):")
        for k, v in pass_at_k.items():
            print(f"    pass@{k}: {v:.2%}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate per-comment analytics from a multi-run results directory. "
            "Each instance subfolder may contain multiple result_run_N.json files."
        )
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results_agent_testgen_multi"),
        help="Directory containing instance subfolders with result_run_N.json files.",
    )
    parser.add_argument(
        "--output-runs-csv",
        type=Path,
        default=None,
        help=(
            "Where to write the per-run CSV. "
            "Defaults to <results-dir>/run_summary.csv."
        ),
    )
    parser.add_argument(
        "--output-comments-csv",
        type=Path,
        default=None,
        help=(
            "Where to write the per-comment aggregated CSV. "
            "Defaults to <results-dir>/comment_summary.csv."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_dir = args.results_dir.resolve()

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory does not exist: {results_dir}")
    if not results_dir.is_dir():
        raise NotADirectoryError(f"Results path is not a directory: {results_dir}")

    runs_csv = (
        args.output_runs_csv.resolve()
        if args.output_runs_csv is not None
        else results_dir / "run_summary.csv"
    )
    comments_csv = (
        args.output_comments_csv.resolve()
        if args.output_comments_csv is not None
        else results_dir / "comment_summary.csv"
    )

    run_df = build_run_df(results_dir)
    comment_df = build_comment_df(run_df)

    runs_csv.parent.mkdir(parents=True, exist_ok=True)
    comments_csv.parent.mkdir(parents=True, exist_ok=True)
    run_df.to_csv(runs_csv, index=False)
    comment_df.to_csv(comments_csv, index=False)

    print_overall_summary(run_df, comment_df)
    print()
    print(f"Per-run CSV written to:      {runs_csv}")
    print(f"Per-comment CSV written to:  {comments_csv}")


if __name__ == "__main__":
    main()
