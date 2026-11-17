import pytest

from sympy import symbols
from sympy.logic.boolalg import SOPform, POSform


def test_sopform_posform_accept_dict_terms_with_partial_specification():
    w, x, y, z = symbols("w x y z")

    # Dict-based terms (possibly partially specified) should be accepted and
    # expanded over unspecified variables.
    #
    # Before fix: dicts are treated as iterables; list(dict) gives keys (Symbols),
    # leading to bogus term lists and ultimately to TypeError/incorrect behavior.
    # After fix: dicts are expanded to full-length 0/1 lists and processed.
    sop = SOPform([w, x, y, z], [{w: 0, x: 1}, {y: 1, z: 1, x: 0}])
    assert str(sop) == "(x & ~w) | (y & z & ~x)", (
        "SOPform should accept dict terms (including partially specified dicts) "
        "and produce the expected minimized expression."
    )

    pos = POSform([w, x, y, z], [{w: 0, x: 1}, {y: 1, z: 1, x: 0}])
    assert str(pos) == "(x | y) & (x | z) & (~w | ~x)", (
        "POSform should accept dict terms (including partially specified dicts) "
        "and produce the expected minimized expression."
    )