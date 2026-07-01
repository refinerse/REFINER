#!/usr/bin/env python3
"""
Analysis: intent alignment, validation-test proxy correctness, and their effect
on the resolved rate.

Five questions (per comment = (instance_id, comment_index)):
  A. How well does classified intent align with groundtruth intent?
  B. How often is a validation test a *correct proxy* (fails on current code AND
     passes once the human gt patch is applied)?
  C. Does intent correctness change the per-comment resolved rate?
  D. Does validation-test correctness change the per-comment resolved rate?
  E. Joint 2x2 of intent correctness x VT proxy correctness.

The qwen-3.6-plus family ran four separate resolution variants (baseline / +intent
/ +VT / REFINER). The flash and claude families are analyzed from a single full
"vt_sk" pipeline run (validation-test + skeleton/intent = the REFINER equivalent);
sections C/D/E simply partition that one run by intent- and VT-correctness.

Edit FAMILIES below to add/adjust runs. Reads existing JSON only — no Docker,
checkouts, or network.
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INTENT_GT = ROOT / "dataset/comment_task_gt.jsonl"

# The canonical set of comments actually handled by the agents. The GT intent file
# lists 485 comments, but only 483 are present across the combined resolution run.
# We treat the comments scored in this folder as the standard universe so every
# section (intent, testgen, resolution) is computed over the same 483 comments.
STANDARD_DIR = ROOT / "agent_resolution_combined"

# Each family: classified-intent jsonl, testgen dir (with GT-patch check), and an
# ordered map of resolution runs {label -> dir}. For families with a single full
# pipeline run, that run is reused for C (intent), D (VT) and E (joint).
FAMILIES = {
    "qwen-3.6-plus": {
        "intent": ROOT / "task_classification/comment_task_qwen.jsonl",
        "testgen": ROOT / "results_testgen_merged_retry_4",
        "runs": {
            "baseline": ROOT / "agents_results/results_agent_resolution_pure_qwen_merged",
            "+intent":  ROOT / "results_vt_intent_merged",
            "+VT":      ROOT / "agents_results/results_agent_resolution_validation_test_merged",
            "REFINER":  ROOT / "results_vt_intent_merged_4",
        },
    },
    "qwen-3.6-flash": {
        "intent": ROOT / "task_classification/comment_task_qwen36flash.jsonl",
        "testgen": ROOT / "results_testgen_qwen36flash_merged",
        "runs": {
            "vt_sk (REFINER)": ROOT / "results_vt_sk_qwen36flash_final",
        },
    },
    "claude-sonnet-4.6": {
        "intent": ROOT / "results_pipeline_funnel/comment_intent_claude_merged.jsonl",
        "testgen": ROOT / "results_claude_testgen_merged_regen40",
        "runs": {
            "vt_sk (REFINER)": ROOT / "results_vt_sk_claude_merged_final",
        },
    },
}

LABELS5 = ["Bugfix", "Refactoring", "Documentation", "Logging", "Others"]


def norm(label):
    """Normalize a label; fold Logging into Others (the 4 task-types the agent sees)."""
    if not label:
        return None
    l = label.strip().capitalize()
    mapping = {"Bugfix": "Bugfix", "Refactoring": "Refactoring",
               "Documentation": "Documentation", "Logging": "Others",
               "Other": "Others", "Others": "Others"}
    return mapping.get(l, l)


def load_intent(path):
    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            key = (d["instance_id"], int(d["comment_index"]))
            out[key] = d.get("label")
    return out


def load_resolution(dir_path):
    """(iid, cidx) -> passed (bool). Uses groundtruth_assessment.results[].passed."""
    out = {}
    if not dir_path.exists():
        return out
    for rj in dir_path.glob("*/result.json"):
        try:
            d = json.loads(rj.read_text())
        except Exception:
            continue
        iid = d.get("instance_id") or rj.parent.name
        ga = d.get("groundtruth_assessment") or {}
        results = ga.get("results")
        if results is None:
            results = d.get("results", [])
        for item in results:
            if not isinstance(item, dict):
                continue
            cidx = item.get("comment_index")
            if cidx is None:
                continue
            passed = item.get("passed")
            if passed is None:
                passed = item.get("test_passed")
            out[(iid, int(cidx))] = (passed is True)
    return out


def load_standard_keys(dir_path):
    """The canonical comment universe: every (iid, cidx) scored in the combined run."""
    keys = set()
    if not dir_path.exists():
        return keys
    for rj in dir_path.glob("*/result.json"):
        try:
            d = json.loads(rj.read_text())
        except Exception:
            continue
        iid = d.get("instance_id") or rj.parent.name
        ga = d.get("groundtruth_assessment") or {}
        results = ga.get("results")
        if results is None:
            results = d.get("results", [])
        for item in results:
            if not isinstance(item, dict):
                continue
            cidx = item.get("comment_index")
            if cidx is None:
                continue
            keys.add((iid, int(cidx)))
    return keys


def load_testgen(dir_path):
    """(iid, cidx) -> dict(has_test, fails_on_current, gt_patch_passed, proxy_correct)."""
    out = {}
    if not dir_path.exists():
        return out
    for rj in dir_path.glob("*/result.json"):
        try:
            d = json.loads(rj.read_text())
        except Exception:
            continue
        iid = d.get("instance_id") or rj.parent.name
        for item in d.get("results", []):
            if not isinstance(item, dict):
                continue
            cidx = item.get("comment_index")
            if cidx is None:
                continue
            assess = item.get("assessment") or {}
            out[(iid, int(cidx))] = {
                "has_test": True,
                # test reliably fails on the unfixed code under review
                "fails_on_current": item.get("expected_failure_observed") is True
                                    or item.get("current_passed") is False,
                "success": item.get("success") is True,
                "gt_patch_passed": assess.get("ground_truth_patch_passed") is True,
                # the strict proxy-validity signal: fails before, passes on gt patch
                "proxy_correct": assess.get("current_fails_and_patch_passes") is True,
            }
    return out


def pct(n, d):
    return f"{100*n/d:5.1f}% ({n}/{d})" if d else "  n/a (0/0)"


def analyze_family(name, cfg, gt, standard):
    qwen = load_intent(cfg["intent"])
    tg = load_testgen(cfg["testgen"])
    runs = {k: load_resolution(v) for k, v in cfg["runs"].items()}

    # Restrict every signal to the canonical comment universe (the 483 comments
    # scored in agent_resolution_combined). If the standard set is empty (folder
    # missing) fall back to the un-restricted behavior.
    if standard:
        qwen = {k: v for k, v in qwen.items() if k in standard}
        gt = {k: v for k, v in gt.items() if k in standard}
        tg = {k: v for k, v in tg.items() if k in standard}
        runs = {lbl: {k: v for k, v in res.items() if k in standard}
                for lbl, res in runs.items()}

    lines = []
    def p(s=""):
        lines.append(s)

    p("#" * 78)
    p(f"# FAMILY: {name}")
    p(f"#   intent  : {cfg['intent'].relative_to(ROOT)}")
    p(f"#   testgen : {cfg['testgen'].relative_to(ROOT)}")
    for lbl, d in cfg["runs"].items():
        p(f"#   run[{lbl}] : {d.relative_to(ROOT)}")
    if standard:
        p(f"#   universe: {len(standard)} comments handled in {STANDARD_DIR.name}")
    p("#" * 78)
    p("")

    p("=" * 78)
    p("A. INTENT ALIGNMENT  (classified  vs  groundtruth)")
    p("=" * 78)
    keys = sorted(set(qwen) & set(gt))
    p(f"classified comments : {len(qwen)}")
    p(f"groundtruth comments: {len(gt)}")
    p(f"overlap (scored)    : {len(keys)}")
    p("")

    correct5 = sum(1 for k in keys if (qwen[k] or "").capitalize() == (gt[k] or "").capitalize())
    correct4 = sum(1 for k in keys if norm(qwen[k]) == norm(gt[k]))
    p(f"Raw 5-class accuracy        : {pct(correct5, len(keys))}")
    p(f"Normalized 4-class accuracy : {pct(correct4, len(keys))}  (Logging folded into Others)")
    p("")

    p("Confusion matrix  (rows = GT, cols = prediction), normalized 4-class:")
    cats = ["Bugfix", "Refactoring", "Documentation", "Others"]
    cm = defaultdict(Counter)
    for k in keys:
        cm[norm(gt[k])][norm(qwen[k])] += 1
    header = "  GT \\ pred   " + "".join(f"{c[:5]:>8}" for c in cats) + f"{'total':>8}"
    p(header)
    for r in cats:
        row_total = sum(cm[r].values())
        cells = "".join(f"{cm[r][c]:>8}" for c in cats)
        p(f"  {r[:11]:<11}" + cells + f"{row_total:>8}")
    p("")
    p("Per-type accuracy (of comments truly of that type, how many classified correctly):")
    for c in cats:
        type_total = sum(cm[c].values())
        p(f"  {c:<13}: {pct(cm[c][c], type_total)}")
    p("")

    p("=" * 78)
    p(f"B. VALIDATION-TEST PROXY CORRECTNESS  ({cfg['testgen'].name})")
    p("=" * 78)
    n_tests = len(tg)
    # Denominator is the full comment universe (483), not just comments that got a
    # test: a comment with no generated test counts as a proxy failure for all rows.
    denom = len(standard) if standard else len(keys)
    n_fail_cur = sum(1 for v in tg.values() if v["fails_on_current"])
    n_gt_pass = sum(1 for v in tg.values() if v["gt_patch_passed"])
    n_proxy = sum(1 for v in tg.values() if v["proxy_correct"])
    p(f"comments in universe                      : {denom}")
    p(f"comments with a generated validation test : {n_tests}")
    p(f"  fails on current code (catches issue)   : {pct(n_fail_cur, denom)}")
    p(f"  passes when GT patch applied            : {pct(n_gt_pass, denom)}")
    p(f"  PROXY-CORRECT (fails now AND gt passes) : {pct(n_proxy, denom)}")
    p("")

    p("=" * 78)
    p("C. INTENT CORRECTNESS  ->  RESOLVED RATE")
    p("=" * 78)
    p("Per comment, intent_correct = (normalized label == normalized GT label).")
    p("")
    for run_label, res in runs.items():
        if not res:
            p(f"[{run_label}] no results loaded, skipping.")
            continue
        groups = {"intent correct": [], "intent wrong": []}
        for k, passed in res.items():
            if k not in qwen or k not in gt:
                continue
            grp = "intent correct" if norm(qwen[k]) == norm(gt[k]) else "intent wrong"
            groups[grp].append(passed)
        p(f"[{run_label}]")
        for grp, vals in groups.items():
            p(f"   {grp:<16}: resolve rate {pct(sum(vals), len(vals))}")
        p("")

    p("=" * 78)
    p("D. VALIDATION-TEST CORRECTNESS  ->  RESOLVED RATE")
    p("=" * 78)
    p("Per comment, bucketed by its validation test's proxy quality.")
    p("")
    for run_label, res in runs.items():
        if not res:
            p(f"[{run_label}] no results loaded, skipping.")
            continue
        groups = {"proxy-correct test": [], "weak/leaky test": [], "no test generated": []}
        for k, passed in res.items():
            v = tg.get(k)
            if v is None:
                grp = "no test generated"
            elif v["proxy_correct"]:
                grp = "proxy-correct test"
            else:
                grp = "weak/leaky test"
            groups[grp].append(passed)
        p(f"[{run_label}]")
        for grp, vals in groups.items():
            p(f"   {grp:<20}: resolve rate {pct(sum(vals), len(vals))}")
        p("")

    p("=" * 78)
    p("E. JOINT 2x2:  intent correctness x VT proxy correctness")
    p("=" * 78)
    # Use the last (most complete) run for the joint table.
    joint_label = list(runs.keys())[-1] if runs else None
    res = runs.get(joint_label) if joint_label else None
    if res:
        p(f"[{joint_label}]")
        cell = defaultdict(list)
        for k, passed in res.items():
            if k not in qwen or k not in gt:
                continue
            ic = "intentOK " if norm(qwen[k]) == norm(gt[k]) else "intentBAD"
            v = tg.get(k)
            vc = "vtOK " if (v and v["proxy_correct"]) else "vtBAD"
            cell[(ic, vc)].append(passed)
        p(f"   {'':<10}{'vtOK':>16}{'vtBAD':>16}")
        for ic in ["intentOK ", "intentBAD"]:
            a = cell[(ic, "vtOK ")]
            b = cell[(ic, "vtBAD")]
            p(f"   {ic:<10}{pct(sum(a),len(a)):>16}{pct(sum(b),len(b)):>16}")
    p("")

    return "\n".join(lines)


def main():
    import sys
    gt = load_intent(INTENT_GT)
    standard = load_standard_keys(STANDARD_DIR)
    selected = sys.argv[1:] or list(FAMILIES.keys())

    all_reports = []
    for name in selected:
        if name not in FAMILIES:
            print(f"[skip] unknown family '{name}' (known: {list(FAMILIES)})")
            continue
        rep = analyze_family(name, FAMILIES[name], gt, standard)
        print(rep)
        print()
        all_reports.append(rep)
        out_path = ROOT / f"intent_vt_effect_report_{name}.txt"
        out_path.write_text(rep + "\n")
        print(f"[written to {out_path}]\n")

    combined = ROOT / "intent_vt_effect_report.txt"
    combined.write_text("\n\n".join(all_reports) + "\n")
    print(f"[combined report written to {combined}]")


if __name__ == "__main__":
    main()
