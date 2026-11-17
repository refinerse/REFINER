import inspect

from sympy.functions.special.hyper import hyper


def test_hyper_eval_nseries_uses_explicit_super_call():
    """
    The implementation was changed from `super()._eval_nseries(...)` to
    `super(hyper, self)._eval_nseries(...)`. This test asserts that the
    explicit two-argument form is used.
    """
    src = inspect.getsource(hyper._eval_nseries)
    assert "super(hyper, self)._eval_nseries" in src, (
        "hyper._eval_nseries should delegate using explicit "
        "`super(hyper, self)._eval_nseries(...)` (two-argument super)."
    )
    assert "super()._eval_nseries" not in src, (
        "hyper._eval_nseries should not use zero-argument `super()` for "
        "delegation in this method."
    )