import re


def test_groupby_fillna_axis1_uses_apply_even_with_value_scalar():
    source = open("/workspace/dask/dataframe/groupby.py").read()

    # Behavior change: GroupBy.fillna should always use apply (row-wise semantics)
    # and never dispatch to transform based on `value is not None` or `axis == 0`.
    assert "def fillna(self, value=None, method=None, limit=None, axis=None):" in source

    # BEFORE code had a branch:
    #   axis = DataFrame._validate_axis(axis)
    #   if value is not None or axis == 0:
    #       ... self.transform(... axis=0) ...
    #   else:
    #       ... self.apply(... axis=1) ...
    #
    # AFTER code removed this branch and always uses self.apply with a helper
    # that drops the grouped-by columns.
    assert (
        "if value is not None or axis == 0" not in source
    ), "GroupBy.fillna should not branch to transform when value is provided; it should use apply consistently (including for axis=1)."

    # Ensure we are actually using the apply-based implementation.
    assert re.search(
        r"\bmeta\s*=\s*self\._meta_nonempty\.apply\s*\(",
        source,
    ), "Expected GroupBy.fillna to build meta via self._meta_nonempty.apply(...)"

    assert re.search(
        r"\bresult\s*=\s*self\.apply\s*\(",
        source,
    ), "Expected GroupBy.fillna to compute via self.apply(...) (not self.transform(...))"

    # The apply helper should drop grouped-by columns (pandas consistency).
    assert (
        "def _fillna_group(" in source
    ), "Expected new helper _fillna_group(...) used by GroupBy.fillna"
    assert (
        ".drop(columns=by)" in source
    ), "Expected _fillna_group to drop grouped-by columns via .drop(columns=by) before fillna"