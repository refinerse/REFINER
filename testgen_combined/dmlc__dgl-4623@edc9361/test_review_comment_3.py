import pytest


def test_exchange_graph_data_callsite_has_no_backslash_between_parentheses():
    """
    The review comment is about removing explicit line-continuation backslashes
    within a parenthesized call.

    The specific hunk shows the call in exchange_graph_data changed from using
    backslashes for line breaks to not using them.

    This test asserts that the exact anti-pattern from the "before" version:
        exchange_node_features(..., \\
            ..., ..., ..., \\
    is not present anymore.

    It must fail on the "before" version (pattern present) and pass on the
    "after" version (pattern absent).
    """
    source = open("/workspace/tools/distpartitioning/data_shuffle.py", "r", encoding="utf-8").read()

    # This exact substring (including the trailing ", \\" after node_features)
    # appears in the BEFORE code (per diff hunk) but not in the AFTER code.
    bad_snippet = (
        "exchange_node_features(rank, world_size, node_feat_tids, \\\n"
        "                                                ntypes_gnid_range_map, id_lookup, node_features, \\\n"
    )

    assert bad_snippet not in source, (
        "exchange_graph_data still contains a parenthesized exchange_node_features(...) call "
        "that uses explicit line-continuation backslashes. The review requested removing "
        "the `\\` between parentheses."
    )

    # Strong check: ensure we still have an exchange_*features call for nodes,
    # just without the backslashes.
    assert "exchange_features(rank, world_size, node_feat_tids" in source or (
        "exchange_node_features(rank, world_size, node_feat_tids" in source
    ), "Expected exchange_graph_data to call a feature exchange function for node features."