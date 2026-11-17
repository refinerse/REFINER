import pytest

from sympy.polys import ring, ZZ


def test_dup_zz_mignotte_bound_has_binomial_available_at_runtime():
    """
    Regression test: dup_zz_mignotte_bound must not crash with NameError
    due to missing `binomial` (previously happened because binomial
    was not imported and/or due to circular import issues).

    The correct implementation should return an even integer-like value
    (SymPy Integer is acceptable).
    """
    R, x = ring("x", ZZ)
    f = x**3 + 14*x**2 + 56*x + 64

    try:
        bound = R.dup_zz_mignotte_bound(f)
    except NameError as e:
        pytest.fail(
            "dup_zz_mignotte_bound raised NameError (likely 'binomial' not defined). "
            "Expected the function to import `binomial` inside the function to "
            "avoid circular import issues and missing names. "
            f"Original error: {e!r}"
        )

    assert bound == 152, (
        "dup_zz_mignotte_bound should compute the Knuth-Cohen Mignotte bound; "
        "expected 152 for f = x**3 + 14*x**2 + 56*x + 64."
    )

    # Don't require a built-in int: SymPy commonly returns sympy.Integer.
    assert bound.is_integer is True, "Expected an integer (or SymPy Integer) bound."
    assert bound % 2 == 0, "Expected the bound to be rounded up to an even integer."
    assert int(bound) == 152, "Expected the bound to be exactly 152 when coerced to int."