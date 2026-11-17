import inspect

import pandas.tests.test_multilevel as tml


def test_subsets_multiindex_dtype_uses_assert_series_equal():
    """
    Functional-ish check for the review change: the new test implementation should
    assign `expected` and `result` and compare them with `tm.assert_series_equal`.

    We can't reliably observe the difference at runtime (both old and new test
    implementations pass), so we inspect the function source to ensure the
    requested assertion helper is used.
    """
    src = inspect.getsource(tml.TestMultiLevel.test_subsets_multiindex_dtype)

    assert "tm.assert_series_equal" in src, (
        "Expected TestMultiLevel.test_subsets_multiindex_dtype to use "
        "tm.assert_series_equal(result, expected) as requested in code review, "
        "but it did not."
    )
    assert "expected =" in src and "result =" in src, (
        "Expected TestMultiLevel.test_subsets_multiindex_dtype to assign variables "
        "`expected =` and `result =` before comparing, as requested in code review."
    )