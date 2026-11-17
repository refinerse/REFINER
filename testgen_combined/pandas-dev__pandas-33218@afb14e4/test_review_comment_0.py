def test_groupby_dataframe_wrap_applied_output_retains_squeeze_logic_until_2_0():
    source = open("/workspace/pandas/core/groupby/generic.py", encoding="utf-8").read()

    # We cannot import pandas in this environment, so we assert on the source.
    # The review discussion indicates that the `squeeze` deprecation/removal
    # must NOT happen until pandas 2.0, so the code handling `self.squeeze`
    # (including computing `applied_index`) must remain present.
    expected = "applied_index = self._selected_obj._get_axis(self.axis)"

    assert expected in source, (
        "Expected DataFrameGroupBy._wrap_applied_output to retain the squeeze "
        "compatibility logic until pandas 2.0.\n"
        "Missing source line:\n"
        f"    {expected}\n"
    )