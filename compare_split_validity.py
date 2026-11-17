#!/usr/bin/env python3
"""Compare split-test validity against the baseline gt-validation results.

Flags any (instance, comment_index) test that was valid in the baseline
(``results_gt_validation``) but is NOT valid in the split run
(``results_gt_validation_splitted``) -- i.e. a regression introduced by
splitting. Also reports per-assertion tallies from the split run.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path("results_gt_validation")
SPLIT = Path("results_gt_validation_splitted")


def load(d: Path) -> dict[str, dict]:
    out = {}
    for rj in d.glob("*/result.json"):
        r = json.loads(rj.read_text())
        rows = {row["comment_index"]: row for row in r.get("results", [])}
        out[r["instance_id"]] = rows
    return out


def main() -> None:
    base = load(BASE)
    split = load(SPLIT)

    regressions = []  # valid in baseline, not valid in split
    missing = []      # baseline-valid test absent from split run
    new_invalid = []  # invalid in split for any reason
    total_base_valid = total_split_valid = 0

    for iid, brows in base.items():
        srows = split.get(iid)
        for ci, brow in brows.items():
            if brow.get("valid"):
                total_base_valid += 1
            if srows is None or ci not in srows:
                if brow.get("valid"):
                    missing.append((iid, ci))
                continue
            srow = srows[ci]
            if srow.get("valid"):
                total_split_valid += 1
            if brow.get("valid") and not srow.get("valid"):
                regressions.append((iid, ci, srow))

    print(f"baseline valid tests : {total_base_valid}")
    print(f"split    valid tests : {total_split_valid}")
    print(f"regressions (valid->invalid after split): {len(regressions)}")
    print(f"baseline-valid tests missing from split run: {len(missing)}")
    for iid, ci in missing[:20]:
        print(f"  MISSING {iid} #{ci}")
    for iid, ci, srow in regressions:
        print(f"\n=== REGRESSION {iid} #{ci} ({srow.get('test_file')}) ===")
        print(f"  passed_on_head={srow.get('passed_on_head')} "
              f"passed_on_merged={srow.get('passed_on_merged')} "
              f"head[{srow.get('head_passed')}P/{srow.get('head_failed')}F] "
              f"merged[{srow.get('merged_passed')}P/{srow.get('merged_failed')}F]")

    # dump regression ids for a targeted re-run / fix
    Path("split_regressions.txt").write_text(
        "\n".join(sorted({iid for iid, _, _ in regressions}))
    )


if __name__ == "__main__":
    main()
