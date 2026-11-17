#!/usr/bin/env python3
"""MR-3: per-PR statistical tests, REFINER vs the vanilla agent and vs Guo et al.

For each backbone and baseline:
  - one-sided Wilcoxon signed-rank test on per-PR resolution rates
    (H1: REFINER > baseline; PRs with equal rates are dropped, as in scipy's default)
  - matched-pairs rank-biserial correlation as the effect size
  - 95% CI of the difference in comment resolution rate (pp), from a bootstrap
    that resamples PRs, so comments of the same PR stay together
  - Holm-adjusted p-values over all comparisons

Usage:
  uv run --with scipy python analyze_statistics.py
"""

from __future__ import annotations

import argparse
import random

from scipy.stats import rankdata, wilcoxon

from analyze_validation_tests import AGENTS_RESULTS, gt_passed

# backbone -> {approach: run dir}
RUNS = {
    "Qwen-3.6-Flash": {
        "REFINER": "pure_qwen_3.6_flash_with_task_and_validation_test",
        "Vanilla agent": "pure_qwen_3.6_flash_baseline",
        "Guo et al.": "icse_intention_with_3.6_flash",
    },
    "Qwen-3.6-Plus": {
        "REFINER": "pure_qwen_3.6_plus_with_task_and_validation_test",
        "Vanilla agent": "pure_qwen_3.6_plus",
        "Guo et al.": "icse_intention",
    },
    "Claude-Sonnet-4.6": {
        "REFINER": "claude_with_task_and_validation_test",
        "Vanilla agent": "pure_claude_code",
        "Guo et al.": "icse_intention_with_4.6_sonnet",
    },
}
BOOTSTRAP_SAMPLES = 10_000
SEED = 0


def per_pr(passed: dict[tuple[str, int], bool], comments: dict[str, list[int]]) -> dict[str, tuple[int, int]]:
    """PR -> (resolved comments, total comments)."""
    return {pr: (sum(passed.get((pr, c), False) for c in idx), len(idx)) for pr, idx in comments.items()}


def rank_biserial(diffs: list[float]) -> float:
    nonzero = [d for d in diffs if d != 0]
    ranks = rankdata([abs(d) for d in nonzero])
    w_plus = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    w_minus = sum(r for r, d in zip(ranks, nonzero) if d < 0)
    return (w_plus - w_minus) / (w_plus + w_minus)


def bootstrap_ci(a: dict[str, tuple[int, int]], b: dict[str, tuple[int, int]], rng: random.Random) -> tuple[float, float]:
    prs = list(a)
    diffs = []
    for _ in range(BOOTSTRAP_SAMPLES):
        sample = rng.choices(prs, k=len(prs))
        total = sum(a[p][1] for p in sample)
        diffs.append((sum(a[p][0] for p in sample) - sum(b[p][0] for p in sample)) / total * 100)
    diffs.sort()
    return diffs[int(0.025 * BOOTSTRAP_SAMPLES)], diffs[int(0.975 * BOOTSTRAP_SAMPLES) - 1]


def holm(pvalues: list[float]) -> list[float]:
    order = sorted(range(len(pvalues)), key=pvalues.__getitem__)
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def self_check() -> None:
    assert rank_biserial([1, 2, 3]) == 1.0
    assert rank_biserial([1, -1]) == 0.0
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    print("self-check ok")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return self_check()

    comments: dict[str, list[int]] = {}
    for pr, idx in gt_passed(AGENTS_RESULTS / "pure_qwen_3.6_plus"):
        comments.setdefault(pr, []).append(idx)
    rng = random.Random(SEED)

    rows = []
    for backbone, runs in RUNS.items():
        refiner = per_pr(gt_passed(AGENTS_RESULTS / runs["REFINER"]), comments)
        for baseline in ("Vanilla agent", "Guo et al."):
            base = per_pr(gt_passed(AGENTS_RESULTS / runs[baseline]), comments)
            diffs = [refiner[p][0] / refiner[p][1] - base[p][0] / base[p][1] for p in comments]
            test = wilcoxon(diffs, alternative="greater")
            total = sum(n for _, n in refiner.values())
            rr_ref = sum(r for r, _ in refiner.values()) / total * 100
            rr_base = sum(r for r, _ in base.values()) / total * 100
            rows.append({
                "backbone": backbone, "baseline": baseline,
                "rr_refiner": rr_ref, "rr_baseline": rr_base, "diff_pp": rr_ref - rr_base,
                "ci": bootstrap_ci(refiner, base, rng),
                "better": sum(d > 0 for d in diffs), "worse": sum(d < 0 for d in diffs), "ties": sum(d == 0 for d in diffs),
                "p": test.pvalue, "r_rb": rank_biserial(diffs),
            })

    for row, p_holm in zip(rows, holm([r["p"] for r in rows])):
        lo, hi = row["ci"]
        print(f"{row['backbone']:18} vs {row['baseline']:14} RR {row['rr_refiner']:.1f} vs {row['rr_baseline']:.1f} "
              f"diff {row['diff_pp']:+.1f} pp [95% CI {lo:+.1f}, {hi:+.1f}]  PRs +{row['better']}/-{row['worse']}/={row['ties']}  "
              f"p={row['p']:.2g} (Holm {p_holm:.2g})  r_rb={row['r_rb']:.2f}")


if __name__ == "__main__":
    main()
