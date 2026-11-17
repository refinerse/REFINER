import re


def test_unused_get_idranges_second_return_is_ignored_for_edges():
    """
    Style regression test for review comment:
    The second return value from get_idranges() for edges (etype_geid_offset) was unused;
    code should ignore it with `_` instead of naming it.

    This test inspects the source because importing the module is not possible in this env.
    """
    source = open("/workspace/tools/distpartitioning/dataset_utils.py", "r", encoding="utf-8").read()

    # BEFORE (bad): edge_tids, etype_geid_offset = get_idranges(...)
    assert "etype_geid_offset" not in source, (
        "Found 'etype_geid_offset' in dataset_utils.py. The review requested not naming an "
        "unused return value from get_idranges(); it should be captured as '_' instead."
    )

    # AFTER (good): edge_tids, _ = get_idranges(...)
    assert re.search(r"\bedge_tids\s*,\s*_\s*=\s*get_idranges\s*\(", source), (
        "Expected the code to ignore the unused second return value from get_idranges for edges "
        "using 'edge_tids, _ = get_idranges(...)', but that pattern was not found."
    )