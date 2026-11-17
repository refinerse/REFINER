import pytest

import src.sqlfluff.rules.std as std


def test_rule_l022_avoids_while_true_loop_for_cte_scan():
    """Rule_L022 should not use a `while True` loop for scanning forward.

    The review request was to avoid `while True` and instead put the loop
    termination logic in the `while` condition. This is a functional safety
    issue because an unconditional loop can hang if no break condition is met.
    """
    source = open("/workspace/src/sqlfluff/rules/std.py", encoding="utf-8").read()

    # Narrow to just the Rule_L022 implementation to avoid false positives from
    # other rules still using `while True` elsewhere in the file.
    start = source.find("class Rule_L022")
    assert start != -1, "Test setup failed: couldn't find Rule_L022 in std.py."
    end = source.find("class Rule_L023", start)
    assert end != -1, "Test setup failed: couldn't find Rule_L023 boundary in std.py."

    rule_l022_source = source[start:end]

    assert (
        "while True:" not in rule_l022_source
    ), "Rule_L022 still contains an unconditional `while True:` loop; loop termination should be in the `while` condition."