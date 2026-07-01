"""Compare per-instance comment coverage between two agent-resolution runs.

The pure-qwen pipeline only includes comments whose single-run Stage 3 test
succeeded (match_tests_to_comments filters on ``success``), while the
mt_vt_sk variants include every comment that got any generated validation
test across the multi-testgen runs. This script counts how often the two
runs ended up prompting the agent with different comment sets for the same
instance, and how each run's coverage compares to the full set of reference
review comments in the dataset.

Comments are parsed from each instance's ``prompt.txt`` artifact, i.e. what
the agent actually saw. Prompt headers look like either:

    ### Comment 1                       (pure qwen — ordinal only)
    ### Comment 1 (dataset index 0)     (mt_vt_sk variants)

When a prompt only has ordinals, dataset indices are unknown and the
comparison for that instance falls back to comment counts.

Usage:
    python compare_comment_coverage.py \
        --left-dir results_agent_resolution_pure_qwen \
        --right-dir results_agent_resolution_mt_vt_sk_any \
        --dataset-file dataset/full_dataset_instances.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

COMMENT_HEADER_RE = re.compile(
    r"^### Comment (\d+)(?: \(dataset index (\d+)\))?\s*$", re.MULTILINE
)


@dataclass
class PromptCoverage:
    """Comments found in one instance's prompt.txt."""

    count: int
    dataset_indices: set[int] | None  # None when the prompt has ordinals only


def parse_prompt_comments(prompt_text: str) -> PromptCoverage:
    """Extract comment count and (when present) dataset indices from a prompt."""
    matches = COMMENT_HEADER_RE.findall(prompt_text)
    indices = {int(idx) for _, idx in matches if idx}
    return PromptCoverage(
        count=len(matches),
        dataset_indices=indices if len(indices) == len(matches) else None,
    )


def load_prompt_coverage(results_dir: Path) -> dict[str, PromptCoverage]:
    """Map instance_id (directory name) -> comments parsed from prompt.txt."""
    coverage: dict[str, PromptCoverage] = {}
    for prompt_file in sorted(results_dir.glob("*/prompt.txt")):
        try:
            text = prompt_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"WARNING: could not read {prompt_file}: {exc}")
            continue
        parsed = parse_prompt_coverage_or_warn(prompt_file, text)
        if parsed is not None:
            coverage[prompt_file.parent.name] = parsed
    return coverage


def parse_prompt_coverage_or_warn(
    prompt_file: Path, text: str
) -> PromptCoverage | None:
    parsed = parse_prompt_comments(text)
    if parsed.count == 0:
        print(f"WARNING: no '### Comment N' headers found in {prompt_file}")
        return None
    return parsed


def load_dataset_comment_counts(dataset_file: Path) -> dict[str, int]:
    """Map instance directory slug -> total number of reference review comments."""
    counts: dict[str, int] = {}
    if not dataset_file.exists():
        print(f"WARNING: dataset file not found: {dataset_file}")
        return counts
    with dataset_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            instance = json.loads(line)
            slug = instance["instance_id"].replace("/", "__")
            counts[slug] = len(instance.get("reference_review_comments", []))
    return counts


def describe(cov: PromptCoverage) -> str:
    if cov.dataset_indices is not None:
        return f"indices={sorted(cov.dataset_indices)}"
    return f"count={cov.count} (ordinals only)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--left-dir", default="results_agent_resolution_pure_qwen",
        help="First results directory (default: pure qwen)",
    )
    parser.add_argument(
        "--right-dir", default="results_agent_resolution_mt_vt_sk_any",
        help="Second results directory (default: mt_vt_sk_any)",
    )
    parser.add_argument(
        "--dataset-file", default="dataset/full_dataset_instances.jsonl",
        help="Dataset JSONL with reference_review_comments per instance",
    )
    parser.add_argument(
        "--list-mismatches", action="store_true",
        help="Print every instance whose prompted comments differ",
    )
    args = parser.parse_args()

    left_dir = Path(args.left_dir)
    right_dir = Path(args.right_dir)
    left = load_prompt_coverage(left_dir)
    right = load_prompt_coverage(right_dir)
    dataset_counts = load_dataset_comment_counts(Path(args.dataset_file))

    common = sorted(set(left) & set(right))
    left_only = sorted(set(left) - set(right))
    right_only = sorted(set(right) - set(left))

    same = []
    left_fewer = []   # left prompts the agent with fewer comments (the issue)
    right_fewer = []
    same_count_diff_indices = []  # equal counts but provably different comments

    for instance_id in common:
        l, r = left[instance_id], right[instance_id]
        if l.dataset_indices is not None and r.dataset_indices is not None:
            if l.dataset_indices == r.dataset_indices:
                same.append(instance_id)
            elif l.dataset_indices < r.dataset_indices:
                left_fewer.append(instance_id)
            elif r.dataset_indices < l.dataset_indices:
                right_fewer.append(instance_id)
            else:
                same_count_diff_indices.append(instance_id)
        else:
            if l.count == r.count:
                same.append(instance_id)
            elif l.count < r.count:
                left_fewer.append(instance_id)
            else:
                right_fewer.append(instance_id)

    mismatched = left_fewer + right_fewer + same_count_diff_indices

    print(f"Left  ({left_dir}): {len(left)} instances with a parseable prompt.txt")
    print(f"Right ({right_dir}): {len(right)} instances with a parseable prompt.txt")
    print(f"Instances in both: {len(common)}")
    print(f"  only in left:  {len(left_only)}")
    print(f"  only in right: {len(right_only)}")
    if not common:
        print("No common instances — nothing to compare.")
        return
    print()
    print(f"Same prompted comments in both:      {len(same):4d} "
          f"({len(same) / len(common):.1%} of common)")
    print(f"Left prompts fewer comments:         {len(left_fewer):4d} "
          f"({len(left_fewer) / len(common):.1%})")
    print(f"Right prompts fewer comments:        {len(right_fewer):4d} "
          f"({len(right_fewer) / len(common):.1%})")
    print(f"Same count, different dataset indices: {len(same_count_diff_indices):4d}")
    print(f"TOTAL instances with differing prompted comments: {len(mismatched):4d} "
          f"({len(mismatched) / len(common):.1%} of common)")

    missing_in_left = sum(
        right[i].count - left[i].count for i in left_fewer
    )
    missing_in_right = sum(
        left[i].count - right[i].count for i in right_fewer
    )
    print()
    print(f"Comments prompted in right but missing from left: {missing_in_left}")
    print(f"Comments prompted in left but missing from right: {missing_in_right}")

    if dataset_counts:
        def coverage_vs_dataset(cov: dict[str, PromptCoverage], name: str) -> None:
            known = [i for i in cov if i in dataset_counts]
            full = sum(1 for i in known if cov[i].count == dataset_counts[i])
            partial = sum(
                1 for i in known if 0 < cov[i].count < dataset_counts[i]
            )
            over = sum(1 for i in known if cov[i].count > dataset_counts[i])
            total_comments = sum(dataset_counts[i] for i in known)
            prompted_comments = sum(cov[i].count for i in known)
            line = (f"{name}: {full} full / {partial} partial coverage of "
                    f"dataset comments ({prompted_comments}/{total_comments} "
                    f"comments, {prompted_comments / total_comments:.1%})")
            if over:
                line += f" / {over} instances prompt MORE comments than the dataset"
            print(line)

        print()
        print("Coverage vs dataset reference_review_comments:")
        coverage_vs_dataset(left, f"  left  ({left_dir})")
        coverage_vs_dataset(right, f"  right ({right_dir})")

    if args.list_mismatches and mismatched:
        print()
        print("Instances with differing prompted comments:")
        for instance_id in sorted(mismatched):
            total = dataset_counts.get(instance_id, "?")
            print(f"  {instance_id}: left {describe(left[instance_id])} | "
                  f"right {describe(right[instance_id])} | dataset_total={total}")


if __name__ == "__main__":
    main()
