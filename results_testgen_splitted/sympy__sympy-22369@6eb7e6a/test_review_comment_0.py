import pytest
from sympy import Symbol
from sympy.geometry.util import find


def test_find_raises_valueerror_when_symbol_not_present_in_equation():
    """
    Regression/style test: find() must not "guess" a value (e.g. return 1)
    when the requested symbol is not a free symbol of the expression.
    """
    y = Symbol("y")
    x = Symbol("x")
    expr = 2*y + 1

    with pytest.raises(ValueError, match=r"could not find"):
        find(x, expr)

    with pytest.raises(ValueError, match=r"could not find"):
        find("x", expr)