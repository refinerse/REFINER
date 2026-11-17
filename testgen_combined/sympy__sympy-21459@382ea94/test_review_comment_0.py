import pytest

import sympy
from sympy import Eq, Function, Symbol


def test_riccati_module_is_algorithm_functions_not_singlepattern_solver_class():
    """
    The riccati module should expose the algorithm as functions (solve_riccati,
    match_riccati, etc.) and should not tie it to dsolve's SinglePatternODESolver
    via a RationalRiccati solver class.
    """
    import sympy.solvers.ode.riccati as riccati

    assert hasattr(riccati, "solve_riccati"), (
        "riccati module should expose a functional API solve_riccati(...) "
        "rather than only a RationalRiccati SinglePatternODESolver class."
    )

    assert not hasattr(riccati, "RationalRiccati"), (
        "riccati module should not define RationalRiccati (a SinglePatternODESolver) "
        "because the Riccati algorithm should not be tied to dsolve's pattern solver class."
    )


def test_solve_riccati_can_solve_simple_riccati_particular_solution():
    import sympy.solvers.ode.riccati as riccati

    x = Symbol("x")
    f = Function("f")
    fx = f(x)

    # Example: x^3 f' - x^2 f - f^2 = 0  =>  f' = f/x + f^2/x^3
    b0 = sympy.S(0)
    b1 = 1 / x
    b2 = 1 / x**3

    sols = riccati.solve_riccati(fx, x, b0, b1, b2)
    assert isinstance(sols, list) and sols, "solve_riccati should return a non-empty list of Eq solutions."
    assert all(isinstance(s, Eq) for s in sols), "solve_riccati should return solutions as Eq(f(x), ...)."