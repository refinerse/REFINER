#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _usage_value(usage: dict[str, Any], key: str) -> float:
    value = usage.get(key, 0)
    return value if isinstance(value, (int, float)) else 0


def _true_count(series: pd.Series) -> int:
    return int(series.eq(True).sum())


def _count_phase_steps(trajectory: Any, phase: str) -> int | None:
    if not isinstance(trajectory, list):
        return None
    phase_steps = [
        step for step in trajectory
        if isinstance(step, dict) and step.get("phase") == phase
    ]
    return len(phase_steps)


def _count_generation_retries(trajectory: Any) -> int | None:
    generate_steps = _count_phase_steps(trajectory, "generate")
    if generate_steps is None:
        return None
    return max(generate_steps - 1, 0)


def summarize_comment_result(
    instance_id: str,
    repo: str | None,
    model: str | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    assessment = result.get("assessment") or {}
    usage = result.get("usage") or {}
    trajectory = result.get("trajectory")
    generation_retries = _count_generation_retries(trajectory)
    regenerate_rounds = _count_phase_steps(trajectory, "regenerate")

    return {
        "instance_id": instance_id,
        "repo": repo,
        "model": model,
        "comment_index": result.get("comment_index"),
        "comment_text": result.get("comment_text"),
        "comment_type": result.get("comment_type"),
        "language": result.get("language"),
        "attempts_used": result.get("attempts_used"),
        "generation_retries": generation_retries,
        "retry_info_available": generation_retries is not None,
        "regeneration_rounds": regenerate_rounds,
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
    result_path = instance_dir / "result.json"
    if not result_path.exists():
        return []

    data = json.loads(result_path.read_text())
    results = data.get("results") or []

    return [
        summarize_comment_result(
            instance_id=instance_dir.name,
            repo=data.get("repo"),
            model=data.get("model"),
            result=result,
        )
        for result in results
    ]


def build_comment_df(results_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for instance_dir in sorted(results_dir.iterdir()):
        if instance_dir.is_dir():
            rows.extend(summarize_instance_dir(instance_dir))

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return df.sort_values(["instance_id", "comment_index"]).reset_index(drop=True)


def build_failed_comment_targets(df: pd.DataFrame) -> pd.DataFrame:
    failed = df[df["ground_truth_patch_passed"] == False].copy()  # noqa: E712 - want literal False only
    if failed.empty:
        return pd.DataFrame(columns=["instance_id", "comment_index"])

    targets = failed.loc[:, ["instance_id", "comment_index"]].copy()
    return targets.sort_values(["instance_id", "comment_index"]).reset_index(drop=True)


def print_overall_summary(df: pd.DataFrame) -> None:
    total_comments = len(df)
    generation_successes = _true_count(df["generation_succeeded"])
    expected_failure_successes = _true_count(df["success"])
    groundtruth_correct = _true_count(df["groundtruth_correct"])
    retry_info_count = _true_count(df["retry_info_available"])

    print(f"Comment rows: {total_comments}")
    print(f"Generation succeeded: {generation_successes}")
    print(f"Expected failure observed: {expected_failure_successes}")
    print(f"Ground-truth correct: {groundtruth_correct}")
    print(
        "Generation success rate: "
        f"{_safe_divide(generation_successes, total_comments):.2%}"
    )
    print(
        "Expected-failure success rate: "
        f"{_safe_divide(expected_failure_successes, total_comments):.2%}"
    )
    print(
        "Ground-truth correctness rate: "
        f"{_safe_divide(groundtruth_correct, total_comments):.2%}"
    )
    if retry_info_count:
        known_retries = pd.to_numeric(df["generation_retries"], errors="coerce").dropna()
        print(f"Rows with retry info: {retry_info_count}")
        print(
            "Average generation retries (known rows): "
            f"{known_retries.mean():.2f}" if not known_retries.empty else
            "Average generation retries (known rows): n/a"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate per-comment analytics from a results directory that contains "
            "one subfolder per instance."
        )
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("agents_results/results_testgen_merged_retry_2"),
        help="Directory containing instance subfolders with result.json files.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help=(
            "Where to write the aggregated CSV. Defaults to "
            "<results-dir>/comment_summary.csv."
        ),
    )
    parser.add_argument(
        "--write-failed-comments",
        type=Path,
        default=None,
        help=(
            "Optional CSV path for failed comment targets (rows where success is "
            "exactly False). Writes instance_id and comment_index columns."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_dir = args.results_dir.resolve()
    output_csv = (
        args.output_csv.resolve()
        if args.output_csv is not None
        else results_dir / "comment_summary.csv"
    )

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory does not exist: {results_dir}")
    if not results_dir.is_dir():
        raise NotADirectoryError(f"Results path is not a directory: {results_dir}")

    df = build_comment_df(results_dir)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    if args.write_failed_comments is not None:
        failed_csv = args.write_failed_comments.resolve()
        failed_csv.parent.mkdir(parents=True, exist_ok=True)
        build_failed_comment_targets(df).to_csv(failed_csv, index=False)

    print_overall_summary(df)
    print(f"CSV written to: {output_csv}")
    if args.write_failed_comments is not None:
        print(f"Failed comment targets written to: {failed_csv}")
    print()
    print("DataFrame preview:")
    # with pd.option_context("display.max_columns", None, "display.width", 240):
    #     print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
