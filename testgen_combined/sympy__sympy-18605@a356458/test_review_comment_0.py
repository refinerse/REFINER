import pytest

from sympy import S
from sympy.tensor.indexed import Idx


def test_idx_infinite_dimension_does_not_use_fuzzy_and_source_guard():
    """
    Regression test for Idx.__new__ infinite dimension check.

    The intended logic is:
        if range is not S.Infinity and fuzzy_not(range.is_integer):
            raise TypeError

    The buggy version used fuzzy_and([...]) and unnecessarily applied fuzzy_not
    to a plain boolean (range is S.Infinity). This test asserts that the
    implementation no longer uses fuzzy_and in that specific check.
    """
    # Functional sanity check: infinite dimension is accepted.
    i = Idx("i", S.Infinity)
    assert i.lower == 0 and i.upper == S.Infinity, (
        "Idx('i', oo) should construct an index with bounds (0, oo)."
    )

    # Source-level check to distinguish before/after: the before version contains
    # the fuzzy_and([...]) pattern here, while the after version does not.
    source = open("/workspace/sympy/tensor/indexed.py", "r", encoding="utf-8").read()
    assert "fuzzy_and([fuzzy_not(range.is_integer), fuzzy_not(range is S.Infinity)])" not in source, (
        "Idx.__new__ should not use fuzzy_and/fuzzy_not on the boolean "
        "'range is S.Infinity'. Expected direct check "
        "'range is not S.Infinity and fuzzy_not(range.is_integer)'."
    )