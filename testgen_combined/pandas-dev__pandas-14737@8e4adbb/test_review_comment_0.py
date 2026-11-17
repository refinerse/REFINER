import pandas as pd


def test_coerce_to_type_no_longer_returns_unused_original():
    """
    The review comment requested removing the unused `original` return value from
    _coerce_to_type. Verify the helper returns exactly (x, dtype), not
    (original, x, dtype).
    """
    from pandas.tools import tile

    x = pd.to_datetime(["2020-01-01", "2020-01-02"]).values

    result = tile._coerce_to_type(x)

    assert isinstance(result, tuple), "_coerce_to_type should return a tuple"
    assert (
        len(result) == 2
    ), "Expected _coerce_to_type to return exactly (x, dtype); the unused `original` must not be returned"

    coerced_x, dtype = result
    assert dtype is not None, "Expected dtype to be set for datetime input"
    assert len(coerced_x) == len(x), "Coerced array should preserve length"