import pytest

from sympy.functions import hyper
from sympy import Symbol


def test_hyper_nseries_expands_in_argument_power_not_series_variable():
    x = Symbol("x")
    y = Symbol("y")

    # Ensure _eval_nseries custom path is used: it checks limit(arg, x->0) == 0.
    # With arg=y*x, limit is 0 so the custom series expansion is constructed.
    expr = hyper((1,), (2,), y * x)

    # Expand in series variable x; the coefficients should involve y**i,
    # not x**i (i.e., no stray x powers beyond the intended x**i from arg**i).
    s = expr.nseries(x, 0, 4).removeO().expand()

    # After the fix: terms are 1 + (y*x)/2 + (y**2*x**2)/6 + (y**3*x**3)/24 + ...
    # Before the fix: terms are 1 + (x)/2 + (x**2)/6 + (x**3)/24 + ... (missing y powers)
    assert s.coeff(x, 1) == y / 2, (
        "hyper((1,),(2,), y*x).nseries(x, 0, 4) should have x^1 coefficient y/2 "
        "(coming from (arg**1)/2 with arg=y*x). This detects whether the implementation "
        "uses arg**i rather than x**i when building the series terms."
    )