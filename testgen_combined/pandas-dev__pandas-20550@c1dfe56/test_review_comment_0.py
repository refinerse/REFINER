import pytest


def test_setitem_mixed_datetime_uses_scalar_dataframe_constructor():
    """
    Enforce the reviewed change: the test should construct df via
    `pd.DataFrame(0, columns=list('ab'), index=range(6))` instead of constructing
    from `np.zeros((6, 2), dtype=int)`.

    We do this by source inspection for the exact constructor call, since the
    change is about how the test is written (and not reliably observable via
    runtime behavior across pandas versions/BlockManager implementations).
    """
    source = open("/workspace/pandas/tests/frame/test_indexing.py", "r", encoding="utf-8").read()

    assert "def test_setitem_mixed_datetime" in source, (
        "Sanity check: expected test_setitem_mixed_datetime to exist in "
        "/workspace/pandas/tests/frame/test_indexing.py"
    )

    assert "pd.DataFrame(0, columns=list('ab'), index=range(6))" in source, (
        "Expected test_setitem_mixed_datetime to construct df with the scalar "
        "DataFrame constructor:\n"
        "    pd.DataFrame(0, columns=list('ab'), index=range(6))\n"
        "as requested in the review comment. This line is missing."
    )

    assert "np.zeros((6, 2), dtype=int)" not in source, (
        "Expected test_setitem_mixed_datetime NOT to construct df from "
        "np.zeros((6, 2), dtype=int), which was the pre-review version and was "
        "reported as failing due to specifying dtype directly."
    )