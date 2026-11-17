import re


def test_groupby_fillna_helper_uses_explicit_args_and_singular_group_name():
    source = open("/workspace/dask/dataframe/groupby.py").read()

    # The review requested:
    # 1) rename helper arg from `groups` -> `group` (single group)
    # 2) replace `**kwargs` with explicit args
    #
    # Before: def _fillna_groups(groups, axis, **kwargs):
    # After:  def _fillna_group(group, by, value, method, limit, fillna_axis):
    assert (
        "def _fillna_group(group, by, value, method, limit, fillna_axis):" in source
    ), (
        "Expected groupby fillna helper to be renamed and to take explicit arguments "
        "(group, by, value, method, limit, fillna_axis). "
        "This fails if the old `_fillna_groups(groups, axis, **kwargs)` helper is still present."
    )

    # Ensure we don't regress back to the kwargs-based helper
    assert (
        re.search(r"def\s+_fillna_groups\s*\(\s*groups\s*,\s*axis\s*,\s*\*\*kwargs\s*\)\s*:", source)
        is None
    ), (
        "Did not expect to find the old `_fillna_groups(groups, axis, **kwargs)` helper; "
        "the helper should use explicit parameters and operate on a single `group`."
    )