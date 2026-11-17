import numpy as np
import pytest

from pandas.core.reshape import tile


def test_coerce_to_type_bool_ndarray_no_nan_check_attributeerror():
    """
    Regression test for bool dtype coercion in _coerce_to_type.

    Before the fix, boolean ndarrays hit a path that used `np.isnan(x)` and
    raised AttributeError for ndarrays. After the fix, bool ndarrays are
    converted to int64 without going through the datetime/timedelta conversion
    branch, so no error is raised and dtype remains None.
    """
    x = np.array([True, False, True], dtype=bool)

    try:
        out, dtype = tile._coerce_to_type(x)
    except AttributeError as err:
        pytest.fail(
            "Boolean ndarray coercion should not raise AttributeError "
            "(e.g. from calling np.isnan on bool ndarray); got: "
            f"{err!r}"
        )

    assert dtype is None, "Bool ndarray should not set a datetime/timedelta dtype"
    assert out.dtype == np.int64, "Bool ndarray should be coerced to int64"
    assert np.array_equal(
        out, np.array([1, 0, 1], dtype=np.int64)
    ), "Bool ndarray values should be converted to 1/0 int64"