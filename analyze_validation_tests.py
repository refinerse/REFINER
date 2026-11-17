#!/usr/bin/env python3
"""MR-4: analyses of REFINER's generated validation tests, per backbone.

  1. Why tests fail on the pre-refined code: failed assertion vs execution error.
  2. Structural vs behavioural tests (classify_validation_tests.py), with the
     vanilla agent's and REFINER's resolution rate on the same comments.
  3. How often the refinement agent revises its own validation test.
  4. Whether a revision weakens the test: assertion lines removed or their
     checked expression changed. Flagged revisions are written to a CSV for
     manual review.

All counts are over the 483 comments that have a ground-truth assessment test.

Usage:
  python analyze_validation_tests.py [--output-dir validation_test_analysis]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from classify_validation_tests import BEHAVIOURAL, STRUCTURAL, classify_file

AGENTS_RESULTS = Path("agents_results")
# backbone -> (testgen dir, vanilla agent dir, REFINER dir)
BACKBONES = {
    "Qwen-3.6-Flash": ("results_testgen_qwen_3.6_flash", "pure_qwen_3.6_flash_baseline", "pure_qwen_3.6_flash_with_task_and_validation_test"),
    "Qwen-3.6-Plus": ("results_testgen_qwen_3.6_plus", "pure_qwen_3.6_plus", "pure_qwen_3.6_plus_with_task_and_validation_test"),
    "Claude-Sonnet-4.6": ("results_testgen_claude_sonnet_4.6", "pure_claude_code", "claude_with_task_and_validation_test"),
}
DEFAULT_OUTPUT_DIR = Path("validation_test_analysis")

ASSERTION_FAILURES = {"AssertionError", "Failed"}  # Failed: pytest.fail / DID NOT RAISE
MISSING_SYMBOL = {"AttributeError", "NameError", "ImportError", "ModuleNotFoundError", "TypeError", "UnboundLocalError", "KeyError"}
UNPARSABLE = {"SyntaxError", "IndentationError"}
ASSERT_LINE = re.compile(r"^\s*(assert\b|self\.assert\w*\(|pytest\.raises\(|with pytest\.raises|expect\()")


def load_results(run_dir: Path) -> dict[tuple[str, int], dict]:
    """(instance_id, comment_index) -> per-comment result, plus the instance-level record."""
    out = {}
    for result_file in run_dir.glob("*/result.json"):
        data = json.loads(result_file.read_text())
        for comment in data.get("results", []):
            out[(result_file.parent.name, int(comment["comment_index"]))] = {"comment": comment, "instance": data}
    return out


def gt_passed(run_dir: Path) -> dict[tuple[str, int], bool]:
    """Ground-truth assessment outcome per comment for one agent run."""
    out = {}
    for key, rec in load_results(run_dir).items():
        assessment = rec["instance"].get("groundtruth_assessment")
        if assessment:
            for r in assessment["results"]:
                out[(key[0], int(r["comment_index"]))] = bool(r["passed"])
        else:
            out[key] = bool(rec["comment"].get("test_passed", rec["comment"].get("resolved")))
    return out


def failure_kind(output: str) -> tuple[str, str]:
    """('assertion'|'execution', exception type) for a failing pytest/jest run."""
    if re.search(r"Test suite failed to run|Cannot use import statement", output):
        return "execution", "SyntaxError"
    if re.search(r"^\s*>?\s*\d*\s*\|?\s*expect\(|Expected|Received", output, re.M) and "Tests:" in output:
        return "assertion", "expect"
    raised = re.findall(r"^E\s+(\w+(?:Error|Exception)|Failed|assert)\b", output, re.M)
    raised = raised or re.findall(r"^(?:FAILED|ERROR) \S+ - (\w+)", output, re.M)
    if not raised:
        return "execution", "unknown"
    exc = "AssertionError" if raised[0] == "assert" else raised[0]
    return ("assertion" if exc in ASSERTION_FAILURES else "execution"), exc


def execution_subtype(exc: str) -> str:
    if exc in MISSING_SYMBOL:
        return "missing symbol/argument"
    if exc in UNPARSABLE:
        return "unparsable"
    return "other"


def split_diff(diff: str) -> dict[int, list[str]]:
    """comment_index -> diff lines for that comment's validation test."""
    out: dict[int, list[str]] = {}
    current = None
    for line in diff.splitlines():
        header = re.match(r"^diff .*test_review_comment_(\d+)\.", line)
        if header:
            current = int(header.group(1))
            out.setdefault(current, [])
        elif current is not None:
            out[current].append(line)
    return out


def weakening_signals(diff_lines: list[str]) -> dict[str, int]:
    removed = [l[1:] for l in diff_lines if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
    removed_asserts = sum(bool(ASSERT_LINE.match(l)) for l in removed)
    added_asserts = sum(bool(ASSERT_LINE.match(l)) for l in added)
    return {
        "removed_asserts": removed_asserts,
        "added_asserts": added_asserts,
        "lines_removed": len(removed),
        "lines_added": len(added),
    }


def rate(n: int, d: int) -> str:
    return f"{n}/{d} ({n / d:.1%})" if d else "0/0"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    gt_keys = set(gt_passed(AGENTS_RESULTS / "pure_qwen_3.6_plus"))
    review_rows = []

    for backbone, (testgen_name, vanilla_name, refiner_name) in BACKBONES.items():
        testgen_dir = AGENTS_RESULTS / testgen_name
        testgen = {k: v["comment"] for k, v in load_results(testgen_dir).items() if k in gt_keys}
        vanilla = gt_passed(AGENTS_RESULTS / vanilla_name)
        refiner = gt_passed(AGENTS_RESULTS / refiner_name)
        refiner_runs = {k: v for k, v in load_results(AGENTS_RESULTS / refiner_name).items() if k in gt_keys}
        print(f"\n===== {backbone} =====")

        # 1. failed assertion vs execution error on the pre-refined code
        failing = {k: c for k, c in testgen.items() if c.get("expected_failure_observed")}
        kinds = {k: failure_kind(c.get("current_output") or "") for k, c in failing.items()}
        n_exec = sum(kind == "execution" for kind, _ in kinds.values())
        print(f"[1] tests failing on pre-refined code: {len(failing)}/{len(gt_keys)}")
        print(f"    failed assertion : {rate(len(failing) - n_exec, len(failing))}")
        print(f"    execution error  : {rate(n_exec, len(failing))}  "
              f"{dict(Counter(execution_subtype(e) for kind, e in kinds.values() if kind == 'execution'))}")

        # 2. structural vs behavioural (REFINER's own generated test for that comment)
        categories = {}
        for k, c in testgen.items():
            path = testgen_dir / c["test_file"] if c.get("test_file") else None
            if path and path.exists():
                categories[k] = classify_file(path)[0]
        print(f"[2] generated tests: {len(categories)} (comments without a test file: {len(gt_keys) - len(categories)})")
        for category in (STRUCTURAL, BEHAVIOURAL):
            keys = [k for k, v in categories.items() if v == category]
            n = len(keys)
            v_pass = sum(vanilla.get(k, False) for k in keys)
            r_pass = sum(refiner.get(k, False) for k in keys)
            print(f"    {category:12} n={n:3}  vanilla {rate(v_pass, n):16} REFINER {rate(r_pass, n):16} "
                  f"({(r_pass - v_pass) / n * 100 if n else 0:+.1f} pp)")

        # 3./4. revisions of the validation test during refinement
        with_test = {k: v for k, v in refiner_runs.items() if v["comment"].get("validation_test_file")}
        revised = {}
        for k, rec in with_test.items():
            per_comment = split_diff(rec["comment"].get("validation_test_diff") or "")
            if per_comment.get(k[1]):
                revised[k] = per_comment[k[1]]
        print(f"[3] tests revised by the refinement agent: {rate(len(revised), len(with_test))}")

        flagged = 0
        for k, lines in revised.items():
            signals = weakening_signals(lines)
            touches_assert = signals["removed_asserts"] > 0
            fewer_asserts = signals["removed_asserts"] > signals["added_asserts"]
            flagged += touches_assert
            review_rows.append({
                "backbone": backbone,
                "instance_id": k[0],
                "comment_index": k[1],
                **signals,
                "touches_assert": touches_assert,
                "fewer_asserts": fewer_asserts,
                "refiner_resolved": refiner.get(k, False),
                "diff": "\n".join(lines),
            })
        print(f"[4] revisions that remove or rewrite an assertion line: {rate(flagged, len(revised))}; "
              f"net fewer assertions: {sum(r['fewer_asserts'] for r in review_rows if r['backbone'] == backbone)}")

    out_csv = args.output_dir / "validation_test_revisions.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)
    print(f"\nwrote {len(review_rows)} revisions to {out_csv}")


if __name__ == "__main__":
    main()
