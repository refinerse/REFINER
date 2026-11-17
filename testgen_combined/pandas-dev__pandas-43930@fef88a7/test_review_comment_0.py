import numpy as np
import pandas as pd
from pandas._libs import NaT


def test_base_index_na_value_for_numpy_datetime64_dtype_is_nat_not_nan():
    """
    Check the behavior of Index._na_value for a *base* Index with a numpy datetime64
    dtype (dtype.kind == "M").

    Regression target:
    - Before fix: base Index._na_value returned np.nan for any np.dtype, including
      datetime64/timedelta64.
    - After fix: base Index._na_value returns NaT for dtype.kind in {"M", "m"}.
    """
    arr = np.array(["2020-01-01", "2020-01-02"], dtype="datetime64[ns]")
    idx = pd.Index(arr)

    assert type(idx) is pd.Index, "Test must exercise the base Index class"
    assert isinstance(idx.dtype, np.dtype), "Expected numpy dtype for base Index"
    assert (
        idx.dtype.kind == "M"
    ), f"Expected datetime64 dtype kind 'M', got {idx.dtype!r}"

    assert (
        idx._na_value is NaT
    ), "Base Index._na_value must be NaT for numpy datetime64 dtypes (not np.nan)"