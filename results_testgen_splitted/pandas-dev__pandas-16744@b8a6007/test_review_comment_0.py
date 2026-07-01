import inspect

import pandas as pd
import pandas.util.testing as tm

import pandas.tests.series.test_datetime_values as mod


def test_test_datetime_understood_asserts_expected_result_not_just_no_exception():
    """
    Ensure the repository's regression test for GH#16726 actually validates the
    computed Series, i.e. it must contain an assert_series_equal/result check.

    This fails on the "before" version because the test body only wraps the
    operation in a try/except and never asserts on the computed result.
    """
    # Locate the test function in the imported module
    cls = mod.TestSeriesDatetimeValues
    assert hasattr(cls, "test_datetime_understood"), (
        "Expected pandas.tests.series.test_datetime_values.TestSeriesDatetimeValues "
        "to define test_datetime_understood"
    )
    fn = cls.test_datetime_understood

    # The improved version must include a real series equality assertion
    src = inspect.getsource(fn)
    assert "assert_series_equal" in src, (
        "test_datetime_understood should compare the computed Series to an expected "
        "Series using assert_series_equal/tm.assert_series_equal; the old version "
        "only tried to catch an exception and would always pass."
    )

    # Additionally, validate the runtime behavior that the test is supposed to cover
    series = pd.Series(pd.date_range("2012-01-01", periods=3))
    offset = pd.offsets.DateOffset(days=6)
    result = series - offset
    expected = pd.Series(pd.to_datetime(["2011-12-26", "2011-12-27", "2011-12-28"]))
    tm.assert_series_equal(
        result,
        expected,
        obj="Subtracting DateOffset(days=6) from a datetime Series should yield the expected dates",
    )