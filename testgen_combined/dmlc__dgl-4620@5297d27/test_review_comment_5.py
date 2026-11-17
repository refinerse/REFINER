import re


def test_exchange_graph_data_call_uses_parentheses_not_backslash_continuations():
    source = open("/workspace/tools/distpartitioning/data_shuffle.py", "r", encoding="utf-8").read()

    # The review comment is about removing "\" in multiline parenthesized calls.
    # We must scope the check to the specific call site in gen_dist_partitions:
    #   node_data, rcvd_node_features, rcvd_global_nids, edge_data  = \
    #                   exchange_graph_data(...)
    #
    # In the "before" code, the exchange_graph_data call continues arguments with "\"
    # at the end of lines (e.g. "node_feat_tids, \\" and "ntypes_gnid_range_map, \\").
    #
    # In the "after" code, that specific call is formatted without those backslashes.
    block_match = re.search(
        r"node_data,\s*rcvd_node_features,\s*rcvd_global_nids,\s*edge_data\s*=\s*\\\s*\n"
        r"(?:[ \t]*.*\n){0,8}?",  # small window after the assignment line
        source,
        flags=re.MULTILINE,
    )
    assert block_match is not None, (
        "Could not locate the gen_dist_partitions assignment block that calls "
        "exchange_graph_data(...). The test expects to find the line "
        "'node_data, rcvd_node_features, rcvd_global_nids, edge_data  = \\' followed "
        "soon by the exchange_graph_data(...) call."
    )

    window = source[block_match.start() : block_match.start() + 800]

    # Find the exchange_graph_data call within that window.
    call_pos = window.find("exchange_graph_data(")
    assert call_pos != -1, (
        "Could not find 'exchange_graph_data(' near the gen_dist_partitions assignment "
        "block. The test is intended to check formatting of that specific call."
    )
    call_window = window[call_pos : call_pos + 500]

    # Fail if the call uses backslash continuations on argument lines (the old style).
    assert "node_feat_tids, \\\n" not in call_window and "ntypes_gnid_range_map, \\\n" not in call_window, (
        "The exchange_graph_data(...) call in gen_dist_partitions still uses backslash "
        "line continuations for its arguments (e.g., 'node_feat_tids, \\' or "
        "'ntypes_gnid_range_map, \\'). The corrected code should rely on parentheses "
        "and not use '\\' there."
    )

    # Positive assertion: the corrected formatting should include a newline after
    # 'node_feat_tids,' without a trailing backslash.
    assert re.search(r"node_feat_tids,\s*\n\s*edge_data", call_window) is not None, (
        "Expected the updated exchange_graph_data(...) call formatting where "
        "'node_feat_tids,' is followed by a newline (no trailing backslash), then "
        "'edge_data, ...'."
    )