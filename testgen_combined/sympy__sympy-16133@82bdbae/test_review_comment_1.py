import pytest

from sympy.logic.boolalg import SOPform, POSform
from sympy import symbols


def test_sop_pos_term_list_length_must_match_number_of_variables():
    w, x, y, z = symbols("w x y z")

    # 4 variables -> each explicit term list/tuple must have length 4.
    bad_minterms = [[1, 0, 1]]  # only 3 bits

    with pytest.raises(ValueError, match=r"must contain 4 bits|contain 4 bits"):
        SOPform([w, x, y, z], bad_minterms)

    with pytest.raises(ValueError, match=r"must contain 4 bits|contain 4 bits"):
        POSform([w, x, y, z], bad_minterms)

    # Sanity: integers should still be accepted as terms.
    expr_sop = SOPform([w, x, y, z], [0, 15])
    expr_pos = POSform([w, x, y, z], [0, 15])
    assert expr_sop is not None and expr_pos is not None, (
        "SOPform/POSform should still accept integer-encoded terms."
    )