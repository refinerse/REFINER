import re


def test_edge_feature_reorder_uses_feature_key_variable():
    """
    Style regression test: ensure we don't repeat `etype_name+'/'+featname` multiple
    times in the edge-feature reordering loop, but instead assign it once to a variable
    (feature_key) and use that variable.

    This must fail on the "before" code (no feature_key; repeated concatenation),
    and pass on the "after" code (feature_key introduced and used).
    """
    source = open("/workspace/tools/distpartitioning/data_shuffle.py", "r", encoding="utf-8").read()

    # Ensure the style fix exists: feature_key assignment in the edge-feature shuffle block.
    assert "feature_key = etype_name+'/'+featname" in source, (
        "Expected edge-feature reordering loop to assign `feature_key = etype_name+'/'+featname` "
        "to avoid repeating the string concatenation."
    )

    # Ensure the old repetition pattern is gone from the edge-feature shuffle block.
    # Specifically, we should not see rcvd_edge_features[etype_name+'/'+featname] anymore.
    assert "rcvd_edge_features[etype_name+'/'+featname]" not in source, (
        "Found repeated `etype_name+'/'+featname` indexing into rcvd_edge_features; "
        "expected code to use `feature_key` instead."
    )

    # Also ensure we don't repeat the concatenation for rcvd_global_eids indexing in that block.
    assert "rcvd_global_eids[etype_name+'/'+featname]" not in source, (
        "Found repeated `etype_name+'/'+featname` indexing into rcvd_global_eids; "
        "expected code to use `feature_key` instead."
    )

    # Sanity: in the edge-feature shuffle block, feature_key should be used for both dicts.
    # (Use simple checks to avoid brittle parsing.)
    assert "assert feature_key in rcvd_global_eids" in source, (
        "Expected edge-feature reordering block to assert membership using `feature_key`."
    )
    assert "global_eids = rcvd_global_eids[feature_key]" in source, (
        "Expected edge-feature reordering block to read global_eids using `feature_key`."
    )
    assert "rcvd_edge_features[feature_key] = rcvd_edge_features[feature_key][feature_idx]" in source, (
        "Expected edge-feature reordering block to reorder features using `feature_key`."
    )