import pytest

from sympy.polys import ring, ZZ
from sympy.core.numbers import Integer


def test_dup_zz_mignotte_bound_handles_binomial_import_and_returns_even_int():
    """
    Regression test for dup_zz_mignotte_bound:
    it should be callable without NameError (binomial must be available),
    and should return an even integer bound.

    This fails on the "before" code because binomial is referenced without
    being imported in dup_zz_mignotte_bound.
    """
    R, x = ring("x", ZZ)
    f = 2*x**2 + 3*x + 4  # simple irreducible candidate over ZZ

    try:
        bound = R.dup_zz_mignotte_bound(f)
    except NameError as e:
        pytest.fail(
            "dup_zz_mignotte_bound should not raise NameError; binomial must be "
            f"imported/available inside the function. Got: {e!r}"
        )

    assert isinstance(bound, (int, Integer)), (
        f"Expected an integer-like bound, got {type(bound)} with value {bound!r}"
    )
    assert int(bound) % 2 == 0, f"Expected an even bound (rounded up to even), got {bound!r}"
    assert int(bound) >= 0, f"Expected a nonnegative bound, got {bound!r}"