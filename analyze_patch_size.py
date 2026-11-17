#!/usr/bin/env python3
"""MR-6: patch size and unrelated edits, per approach and backbone.

  churn          lines added + removed by the agent's final patch
  files          files the patch modifies
  unrelated edit the patch modifies a file the developers do not change when
                 addressing the review, i.e. outside the follow-up changes from the
                 reviewed patch to the merged patch

Rates are over the 339 PRs; churn/files statistics are over non-empty patches.

Usage:
  python analyze_patch_size.py [--output-csv patch_size.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from pathlib import Path

AGENTS_RESULTS = Path("agents_results")
DATASET_FILE = Path("dataset/instances.jsonl")
DEFAULT_OUTPUT_CSV = Path("patch_size.csv")
# (approach, backbone) -> run dir
RUNS = {
    ("Vanilla agent", "Qwen-3.6-Flash"): "pure_qwen_3.6_flash_baseline",
    ("Guo et al.", "Qwen-3.6-Flash"): "icse_intention_with_3.6_flash",
    ("REFINER", "Qwen-3.6-Flash"): "pure_qwen_3.6_flash_with_task_and_validation_test",
    ("Vanilla agent", "Qwen-3.6-Plus"): "pure_qwen_3.6_plus",
    ("Guo et al.", "Qwen-3.6-Plus"): "icse_intention",
    ("REFINER", "Qwen-3.6-Plus"): "pure_qwen_3.6_plus_with_task_and_validation_test",
    ("Vanilla agent", "Claude-Sonnet-4.6"): "pure_claude_code",
    ("Guo et al.", "Claude-Sonnet-4.6"): "icse_intention_with_4.6_sonnet",
    ("REFINER", "Claude-Sonnet-4.6"): "claude_with_task_and_validation_test",
}
DIFF_FILE = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.M)
# The validation tests REFINER writes are not part of the refinement patch.
VALIDATION_TEST = re.compile(r"(^|/)test_review_comment_\d+\.")


def diff_files(diff: str) -> set[str]:
    return {b for _, b in DIFF_FILE.findall(diff or "") if not VALIDATION_TEST.search(b)}


def churn(diff: str) -> int:
    total, skip = 0, False
    for line in (diff or "").splitlines():
        if line.startswith("diff --git"):
            skip = bool(VALIDATION_TEST.search(line))
        elif not skip and line[:1] in "+-" and not line.startswith(("+++", "---")):
            total += 1
    return total


def per_file_diffs(diff: str) -> dict[str, str]:
    """file -> its diff body, without the index line (blob hashes differ between patches)."""
    out: dict[str, list[str]] = {}
    current = None
    for line in (diff or "").splitlines():
        header = DIFF_FILE.match(line)
        if header:
            current = header.group(2)
            out[current] = []
        elif current is not None and not line.startswith("index "):
            out[current].append(line)
    return {f: "\n".join(body) for f, body in out.items()}


def load_fix_files() -> dict[str, set[str]]:
    """PR -> files the developers changed after the review (reviewed patch -> merged patch)."""
    fix_files = {}
    for line in DATASET_FILE.open():
        inst = json.loads(line)
        reviewed = inst["commit_to_review"]
        reviewed = reviewed if isinstance(reviewed, dict) else json.loads(reviewed)
        before = per_file_diffs(reviewed.get("patch_to_review", ""))
        after = per_file_diffs(inst.get("merged_patch", ""))
        fix_files[inst["instance_id"]] = {f for f in before.keys() | after.keys() if before.get(f) != after.get(f)}
    return fix_files


def load_patches(run_dir: Path) -> dict[str, str]:
    patches = {}
    for result_file in run_dir.glob("*/result.json"):
        results = json.loads(result_file.read_text()).get("results") or [{}]
        patches[result_file.parent.name] = results[0].get("agent_diff") or ""
    return patches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    args = parser.parse_args()

    fix_files = load_fix_files()
    rows = []
    print(f"{'backbone':18} {'approach':14} {'PRs':>4} {'empty':>6} {'med churn':>10} {'mean churn':>11} "
          f"{'med files':>10} {'unrelated edit':>16}")
    for (approach, backbone), run_name in RUNS.items():
        patches = load_patches(AGENTS_RESULTS / run_name)
        churns, n_files, unrelated = [], [], 0
        for instance_id, diff in patches.items():
            files = diff_files(diff)
            extra = files - fix_files.get(instance_id, set())
            unrelated += bool(extra)
            if files:
                churns.append(churn(diff))
                n_files.append(len(files))
            rows.append({"backbone": backbone, "approach": approach, "instance_id": instance_id,
                         "churn": churn(diff), "files": len(files), "unrelated_files": ";".join(sorted(extra))})
        n = len(patches)
        print(f"{backbone:18} {approach:14} {n:4} {n - len(churns):6} {statistics.median(churns):10} "
              f"{statistics.mean(churns):11.1f} {statistics.median(n_files):10} "
              f"{unrelated:5}/{n} ({unrelated / n:.1%})")

    with args.output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
