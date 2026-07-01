import pytest

from sympy import S, symbols, solve


def test_issue_21882_regression_solution_count():
    """
    Regression test for issue #21882: solve(equations, unknowns, dict=True)
    should return exactly 3 solution dictionaries (not 4).
    """
    a, b, c, d, f, g, k = unknowns = symbols('a, b, c, d, f, g, k')

    equations = [
        -k*a + b + 5*f/6 + 2*c/9 + 5*d/6 + 4*a/3,
        -k*f + 4*f/3 + d/2,
        -k*d + f/6 + d,
        13*b/18 + 13*c/18 + 13*a/18,
        -k*c + b/2 + 20*c/9 + a,
        -k*b + b + c/18 + a/6,
        5*b/3 + c/3 + a,
        2*b/3 + 2*c + 4*a/3,
        -g,
    ]

    res = solve(equations, unknowns, dict=True)

    assert res == [
        {a: 0, f: 0, b: 0, d: 0, c: 0, g: 0},
        {a: 0, f: -d, b: 0, k: S(5) / 6, c: 0, g: 0},
        {a: -2 * c, f: 0, b: c, d: 0, k: S(13) / 18, g: 0},
    ], (
        "Expected solve(..., dict=True) for issue #21882 system to return exactly "
        "the 3 canonical solution dictionaries."
    )