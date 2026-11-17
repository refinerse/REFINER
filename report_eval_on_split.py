#!/usr/bin/env python3
"""Summarize patch-verification results across evaluate_agent_patch_on_split.

The split tests are FIXED, so every comment has a fixed number of sub-tests.
That fixed total (sum over all 483 comments) is the SAME denominator for every
agent -- assertions that never ran (patch didn't apply, collection errored) are
counted as failed, not dropped. This keeps assertion totals consistent across
agents.

Columns (per agent):
  c=100%/>=75%/>=50%/>=25% : comments where that fraction of the comment's
                             FIXED sub-tests passed (c=100% == tPass)
  aPass / asserts / aRate  : assertions passed / FIXED total (same for all) / rate
  aRate(cap)               : pass-rate over the comments every agent ran
                             (identical fixed denominator, intersection only)
  fullyOK / applied / err
"""
from __future__ import annotations

import ast
import glob
import json
import re
from pathlib import Path

from run_batch_patch_verification import (
    load_combined_result,
    load_dataset_instances,
    verified_tests_from_result,
)

ROOT = Path("evaluate_agent_patch_on_split")
SPLIT_TESTGEN = "results_testgen_splitted"
DATASET = "dataset/instances.jsonl"
GT_VALIDATION = "results_gt_validation_splitted"

# pytest -v line: "<nodeid>::test_name PASSED [ 50%]" (status AFTER the name).
# Summary lines ("FAILED <nodeid>", status BEFORE the name) deliberately do NOT
# match, so they can't overwrite a real per-test verdict.
_SUBTEST_LINE_RE = re.compile(r"(test\w+)\s+(PASSED|FAILED|ERROR)\b")


def subtest_status(output: str) -> dict[str, bool]:
    """Map sub-test name -> passed? from a pytest ``-v`` output."""
    out: dict[str, bool] = {}
    for line in output.splitlines():
        m = _SUBTEST_LINE_RE.search(line)
        if m:
            out[m.group(1)] = (m.group(2) == "PASSED")
    return out


def subtest_names(code: str, lang: str) -> list[str]:
    """Canonical sub-test function names for a comment's (split) test code."""
    if lang != "python":
        return ["__nonpy__"]
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["__nonpy__"]
    return [n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name.startswith("test")] or ["__nonpy__"]


def canonical_names() -> dict[tuple, list[str]]:
    """(instance_id, comment_index) -> list of fixed sub-test names."""
    out: dict[tuple, list[str]] = {}
    for inst in load_dataset_instances(Path(DATASET)):
        tg = load_combined_result(Path(SPLIT_TESTGEN), inst["instance_id"])
        if tg is None:
            continue
        for vt in verified_tests_from_result(inst, tg):
            out[(inst["instance_id"], vt["comment_index"])] = subtest_names(
                vt["test_code"], vt["language"])
    return out


def p2p_keys(names: dict[tuple, list[str]]) -> set[tuple]:
    """(iid, cidx, subtest_name) that PASSED on head_commit (pre-patch) per the
    gt-validation split run. A sub-test is PASS-TO-PASS only with explicit
    positive evidence; everything else is FAIL-TO-PASS."""
    p2p: set[tuple] = set()
    for rj in glob.glob(str(Path(GT_VALIDATION) / "*" / "result.json")):
        d = json.loads(Path(rj).read_text())
        iid = d["instance_id"]
        for r in d.get("results", []):
            cidx = r.get("comment_index")
            if r.get("language") != "python":
                if r.get("passed_on_head"):
                    p2p.add((iid, cidx, "__nonpy__"))
                continue
            for nm, passed in subtest_status(r.get("head_output", "")).items():
                if passed and nm in names.get((iid, cidx), []):
                    p2p.add((iid, cidx, nm))
    return p2p


def agent_passed_keys(sub: Path) -> set[tuple]:
    """(iid, cidx, subtest_name) that PASSED after the agent's patch."""
    passed: set[tuple] = set()
    for rj in glob.glob(str(sub / "*" / "result.json")):
        d = json.loads(Path(rj).read_text())
        iid = d["instance_id"]
        for r in d.get("results", []):
            cidx = r.get("comment_index")
            if r.get("language") != "python":
                if r.get("test_passed"):
                    passed.add((iid, cidx, "__nonpy__"))
                continue
            for nm, ok in subtest_status(r.get("test_output", "")).items():
                if ok:
                    passed.add((iid, cidx, nm))
    return passed

LABELS = {
    "pure_qwen_3.6_flash_baseline": "pure_qwen_3.6_flash baseline",
    "pure_qwen_3.6_flash_with_task_and_validation_test": "pure_qwen_3.6_flash +task+vt",
    "pure_qwen_3.6_plus": "pure_qwen_3.6_plus baseline",
    "pure_qwen_3.6_plus_with_task": "pure_qwen_3.6_plus +task",
    "pure_qwen_3.6_plus_with_validation_test": "pure_qwen_3.6_plus +vt",
    "pure_qwen_3.6_plus_with_task_and_validation_test": "pure_qwen_3.6_plus +task+vt",
    "icse_intention": "icse intention",
    "pure_claude_code": "pure claude code",
    "claude_with_task_and_validation_test": "claude vt+task",
}
ORDER = ["pure_qwen_3.6_flash_baseline",
         "pure_qwen_3.6_flash_with_task_and_validation_test",
         "pure_qwen_3.6_plus",
         "pure_qwen_3.6_plus_with_task",
         "pure_qwen_3.6_plus_with_validation_test",
         "pure_qwen_3.6_plus_with_task_and_validation_test",
         "icse_intention",
         "pure_claude_code",
         "claude_with_task_and_validation_test"]


def n_subtests(code: str, lang: str) -> int:
    """Fixed number of split sub-tests in a comment's test code."""
    if lang != "python":
        return 1
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 1
    return sum(
        1 for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")
    ) or 1


def fixed_counts() -> dict[tuple, int]:
    """(instance_id, comment_index) -> fixed sub-test count, from split sources."""
    out = {}
    for inst in load_dataset_instances(Path(DATASET)):
        tg = load_combined_result(Path(SPLIT_TESTGEN), inst["instance_id"])
        if tg is None:
            continue
        for vt in verified_tests_from_result(inst, tg):
            out[(inst["instance_id"], vt["comment_index"])] = n_subtests(
                vt["test_code"], vt["language"])
    return out


def load_agent(sub: Path):
    """summary, per-comment {key: (ran, passed)}, fullyOK, applied."""
    summ_path = sub / "summary.json"
    summ = json.loads(summ_path.read_text()) if summ_path.exists() else None
    per_comment: dict[tuple, tuple] = {}
    fully = applied = 0
    for rj in glob.glob(str(sub / "*" / "result.json")):
        d = json.loads(Path(rj).read_text())
        iid = d["instance_id"]
        nt, npass = d.get("num_tests", 0), d.get("num_tests_passed", 0)
        if d.get("patch_applied"):
            applied += 1
        if nt > 0 and npass == nt:
            fully += 1
        for r in d.get("results", []):
            na = r.get("num_assertions")
            if na is None:
                continue
            per_comment[(iid, r.get("comment_index"))] = (na, r.get("assertions_passed", 0))
    return summ, per_comment, fully, applied


def main() -> None:
    FIXED = fixed_counts()
    FIXED_TOTAL = sum(FIXED.values())

    data = {n: (load_agent(ROOT / n) if (ROOT / n / "summary.json").exists() else None)
            for n in ORDER}
    present = [n for n in ORDER if data.get(n)]

    # Comments every present agent actually ran (for the intersection metric).
    common = None
    for n in present:
        ran = {k for k, (na, _) in data[n][1].items() if na > 0}
        common = ran if common is None else (common & ran)
    common = common or set()
    cap_total = sum(FIXED.get(k, 0) for k in common)

    hdr = (f"{'agent':<46}{'c=100%':>7}{'c>=75%':>7}{'c>=50%':>7}{'c>=25%':>7}"
           f"{'aPass':>7}{'asserts':>8}{'aRate':>7}{'aRate(cap)':>11}"
           f"{'fullyOK':>8}{'applied':>8}{'err':>4}")
    print(hdr)
    print("-" * len(hdr))
    for name in ORDER:
        label = LABELS.get(name, name)
        if not data.get(name):
            print(f"{label:<46}{'(no summary.json)':>20}")
            continue
        summ, pc, fully, applied = data[name]
        # per-comment passed, denominated by the FIXED sub-test count
        apass = c100 = c75 = c50 = c25 = 0
        for key, fixed_n in FIXED.items():
            passed = pc.get(key, (0, 0))[1]
            passed = min(passed, fixed_n)
            apass += passed
            frac = passed / fixed_n if fixed_n else 0.0
            if frac >= 1.0:
                c100 += 1
            if frac >= 0.75:
                c75 += 1
            if frac >= 0.50:
                c50 += 1
            if frac >= 0.25:
                c25 += 1
        arate = apass / FIXED_TOTAL if FIXED_TOTAL else 0.0
        cap_pass = sum(min(pc.get(k, (0, 0))[1], FIXED.get(k, 0)) for k in common)
        cap_rate = cap_pass / cap_total if cap_total else 0.0
        print(f"{label:<46}{c100:>7}{c75:>7}{c50:>7}{c25:>7}"
              f"{apass:>7}{FIXED_TOTAL:>8}{arate*100:>6.1f}%{cap_rate*100:>10.1f}%"
              f"{fully:>8}{applied:>8}{summ.get('total_errors', 0):>4}")
    print("-" * len(hdr))
    print(f"asserts = FIXED total {FIXED_TOTAL} sub-tests over all 483 comments "
          f"(SAME denominator for every agent; un-run sub-tests count as failed)")
    print("c=100%/>=75%/>=50%/>=25% = comments where that FRACTION of the comment's "
          "FIXED sub-tests passed (c=100% == tPass; thresholds nest)")
    print(f"aRate     = aPass / {FIXED_TOTAL}")
    print(f"aRate(cap)= pass-rate over the {len(common)} comments ({cap_total} sub-tests) "
          f"that ALL {len(present)} agents ran")

    # ---- Second table: split aPass into FAIL_TO_PASS vs PASS_TO_PASS --------
    NAMES = canonical_names()
    ALL_KEYS = {(iid, cidx, nm) for (iid, cidx), nms in NAMES.items() for nm in nms}
    P2P = p2p_keys(NAMES) & ALL_KEYS          # passed on head (regression guards)
    F2P = ALL_KEYS - P2P                       # failed/errored/absent on head (must fix)
    f2p_total, p2p_total = len(F2P), len(P2P)

    print()
    hdr2 = (f"{'agent':<46}{'F2P_pass':>9}{'F2P_tot':>8}{'F2P%':>7}"
            f"{'P2P_keep':>9}{'P2P_tot':>8}{'P2P_brk':>8}{'aPass':>7}")
    print(hdr2)
    print("-" * len(hdr2))
    for name in ORDER:
        label = LABELS.get(name, name)
        sub = ROOT / name
        if not (sub / "summary.json").exists():
            print(f"{label:<46}{'(no summary.json)':>20}")
            continue
        passed = agent_passed_keys(sub)
        f2p_pass = len(passed & F2P)
        p2p_keep = len(passed & P2P)
        p2p_brk = p2p_total - p2p_keep
        f2p_rate = f2p_pass / f2p_total if f2p_total else 0.0
        print(f"{label:<46}{f2p_pass:>9}{f2p_total:>8}{f2p_rate*100:>6.1f}%"
              f"{p2p_keep:>9}{p2p_total:>8}{p2p_brk:>8}{f2p_pass + p2p_keep:>7}")
    print("-" * len(hdr2))
    print(f"F2P (fail->pass) = {f2p_total} sub-tests that did NOT pass on head_commit "
          f"(the fixes a correct patch must make); F2P% = F2P_pass / {f2p_total}")
    print(f"P2P (pass->pass) = {p2p_total} sub-tests already passing on head_commit "
          f"(regression guards); P2P_brk = P2P that no longer pass (incl. un-applied patches)")
    print(f"aPass = F2P_pass + P2P_keep (name-based; reconciles with table 1's count-based "
          f"aPass to within <=2 sub-tests, from one comment whose pytest summary parses oddly).")
    print(f"Classification: P2P only with an explicit head PASS; ~7 head-collection-error "
          f"sub-tests default to F2P (<=0.5% ambiguity).")


if __name__ == "__main__":
    main()
