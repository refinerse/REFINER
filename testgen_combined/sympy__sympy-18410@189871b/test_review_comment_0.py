import re

import sympy
from sympy.solvers.ode import dsolve, checkodesol


def test_issue_18408_pins_uc_hint_and_tests_exp_plus_sinh_rhs():
    """
    Ensure issue_18408 tests:
    1) explicitly pin hint='nth_linear_constant_coeff_undetermined_coefficients'
    2) include a case where RHS contains both sinh(x) and exp(x)
    and verify SymPy can solve that combined-forcing ODE with that hint.
    """
    x = sympy.Symbol("x")
    f = sympy.Function("f")

    # Functional behavior: solver should handle combined RHS without confusion.
    eq = f(x).diff(x, 3) - f(x).diff(x) - sympy.sinh(x) - sympy.exp(x)
    sol = dsolve(eq, hint="nth_linear_constant_coeff_undetermined_coefficients")
    assert checkodesol(eq, sol) == (True, 0), (
        "dsolve should solve f''' - f' = sinh(x) + exp(x) using "
        "nth_linear_constant_coeff_undetermined_coefficients, and checkodesol "
        "should verify the solution."
    )

    # Source-level check: repo test should pin the hint and include combined RHS case.
    source = open("/workspace/sympy/solvers/tests/test_ode.py", encoding="utf-8").read()
    assert "def test_issue_18408" in source, (
        "Expected test_issue_18408 to exist in /workspace/sympy/solvers/tests/test_ode.py"
    )

    block = source.split("def test_issue_18408", 1)[1]
    block = block.split("\ndef ", 1)[0]

    # All dsolve calls in this block should specify the UC hint explicitly.
    dsolve_calls = re.findall(r"dsolve\((.*?)\)", block, flags=re.S)
    assert dsolve_calls, "Expected at least one dsolve(...) call inside test_issue_18408"
    for call in dsolve_calls:
        assert (
            "hint='nth_linear_constant_coeff_undetermined_coefficients'" in call
            or 'hint="nth_linear_constant_coeff_undetermined_coefficients"' in call
        ), (
            "All dsolve calls in test_issue_18408 should explicitly specify "
            "hint='nth_linear_constant_coeff_undetermined_coefficients' to avoid "
            "solver-selection changes causing test instability."
        )

    # The issue_18408 test should include the combined forcing -sinh(x) - exp(x).
    assert re.search(r"-\s*sinh\(x\)\s*-\s*exp\(x\)", block), (
        "test_issue_18408 should include a case with RHS containing both sinh(x) and exp(x), "
        "i.e. f''' - f' - sinh(x) - exp(x)."
    )