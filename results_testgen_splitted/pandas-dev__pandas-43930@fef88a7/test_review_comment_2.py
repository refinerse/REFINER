import pandas as pd


def test_loc_validate_key_uses_axis_not_index_for_bool_scalar_key():
    """
    When using .loc with axis=1 (columns), a boolean scalar key should be
    validated against the columns axis, not against obj.index.

    This should allow selecting a column labeled True when columns are boolean,
    even if the row index is not boolean.
    """
    df = pd.DataFrame(
        {"a": [1, 2], "b": [3, 4]},
        index=pd.Index(["x", "y"]),  # non-boolean index
    )
    df.columns = pd.Index([True, False], dtype="bool")

    result = df.loc(axis=1)[True]

    # Expected: selecting the column with label True returns a Series
    expected = df[True]

    assert result.equals(expected), (
        "df.loc(axis=1)[True] should select the column labeled True when the "
        "columns axis is boolean, regardless of the (non-boolean) row index."
    )