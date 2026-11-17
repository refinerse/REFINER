import inspect

import sympy.functions.elementary.tests.test_piecewise as tp


def test_issue_21481_uses_python_iterable_and_sympy_half():
    """
    Structural regression test for issue_21481 test content:
    - use a Python iterable (tuple) rather than SymPy Tuple
    - use S.Half rather than float literals 0.5/-0.5

    This inspects the source of the function in the installed module, since the
    change is about test structure/style rather than runtime behavior.
    """
    src = inspect.getsource(tp.test_issue_21481)

    assert "v = (" in src, (
        "test_issue_21481 should use a Python tuple literal for v (e.g. `v = (...)`), "
        "not SymPy's `Tuple(...)`."
    )
    assert "Tuple(" not in src, (
        "test_issue_21481 should not use SymPy `Tuple(...)`; prefer Python iterables."
    )

    assert "S.Half" in src, (
        "test_issue_21481 should use `S.Half` instead of float literals for halves."
    )
    assert "0.5" not in src and "-0.5" not in src, (
        "test_issue_21481 should not contain float literals `0.5` or `-0.5`; "
        "use `S.Half` and `-S.Half`."
    )