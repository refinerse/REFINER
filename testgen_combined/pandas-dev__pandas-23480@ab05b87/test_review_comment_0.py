import pytest


def test_reindex_empty_series_tz_dtype_test_moved_out_of_test_multilevel():
    """
    Review comment requested moving the reindex-related test out of
    pandas/tests/test_multilevel.py into pandas/tests/series.

    This test asserts the moved test is no longer present in
    pandas.tests.test_multilevel.TestMultiLevel.
    """
    import pandas.tests.test_multilevel as tmulti

    assert not hasattr(
        tmulti.TestMultiLevel, "test_reindex_empty_series_tz_dtype"
    ), (
        "Expected reindex-related test 'test_reindex_empty_series_tz_dtype' to be "
        "moved out of /workspace/pandas/tests/test_multilevel.py (per review). "
        "It is still present on TestMultiLevel, so the move was not applied."
    )