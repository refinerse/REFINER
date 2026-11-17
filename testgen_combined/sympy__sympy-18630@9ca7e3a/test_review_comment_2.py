import pytest

from sympy.functions.special.hyper import hyper
from sympy import Symbol, exp, simplify, S


def test_hyper_nseries_uses_argument_not_series_variable():
    x = Symbol("x")

    # Pick an argument that is O(x) at x=0 but not equal to x, so that
    # using x**i vs arg**i is observable in the resulting series.
    expr = hyper([], [], exp(x) - 1)  # equals exp(exp(x) - 1)

    got = expr.nseries(x, 3)  # should be 1 + x + x**2 + O(x**3)
    got_poly = got.removeO()

    # If _eval_nseries incorrectly uses x instead of arg, it produces exp(x).
    # If it correctly uses arg, it produces exp(exp(x) - 1).
    correct_poly = exp(exp(x) - 1).series(x, 0, 3).removeO()
    wrong_poly = exp(x).series(x, 0, 3).removeO()

    assert simplify(got_poly - correct_poly) == S.Zero, (
        "hyper._eval_nseries should expand in powers of the hyper argument (arg**i). "
        "For hyper([], [], exp(x)-1), the series in x should match exp(exp(x)-1) up to O(x**3)."
    )
    assert simplify(got_poly - wrong_poly) != S.Zero, (
        "Regression check: hyper._eval_nseries must not expand as if the argument were x. "
        "That would match exp(x) for hyper([], [], exp(x)-1), which is incorrect."
    )