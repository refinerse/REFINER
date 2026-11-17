import pytest

from sqlfluff.core import Linter


def test_rule_l036_ignores_trailing_whitespace_after_select_before_first_newline():
    """Rule L036 should ignore whitespace *before* the first newline after SELECT.

    Regression for a false-positive where trailing whitespace after SELECT on the
    same line could be mistaken for the indentation whitespace before the first
    select target line.

    This should lint cleanly (no L036 violation) for multi-target SELECT where:
    - the SELECT line ends with trailing spaces
    - then newline
    - then indentation + targets on separate lines
    """
    sql = "SELECT   \n    a,\n    b\nFROM t\n"
    linter = Linter(dialect="ansi", rules=["L036"])
    linted = linter.lint_string(sql)

    l036_violations = [
        v for v in linted.get_violations() if getattr(v, "rule_code", None) == "L036"
    ]

    assert (
        l036_violations == []
    ), "Expected no L036 violations: trailing whitespace after SELECT (before first newline) must be ignored when locating indentation before select targets."