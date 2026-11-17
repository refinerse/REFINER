import re


def test_groupby_fillna_drops_groupby_columns_by_name_not_first_column():
    source = open("/workspace/dask/dataframe/groupby.py", encoding="utf-8").read()

    # Functional intent of the review:
    # Don't always drop the zeroth column in fillna/apply path; instead drop the grouped-by
    # column(s) by name via a helper that accepts a `by` argument.
    assert (
        "groups.drop(columns=groups.columns[0]" not in source
    ), "groupby.fillna should not blindly drop the first column (groups.columns[0]); it must drop the grouped-by column(s) instead."

    # Ensure the refactor introduced a helper that takes `by` and drops those columns.
    assert re.search(r"def\s+_fillna_group\s*\(\s*group\s*,\s*by\s*,", source), (
        "Expected a helper like `_fillna_group(group, by, ...)` so the caller can pass "
        "the actual group-by key(s) and drop the correct columns."
    )
    assert "group.drop(columns=by)" in source, (
        "Expected `_fillna_group` to drop the grouped-by columns via `group.drop(columns=by)` "
        "to handle non-first group keys and multi-column groupby."
    )