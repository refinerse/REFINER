import re


def test_edge_data_truthiness_check_style():
    """
    Style regression test for tools/distpartitioning/dataset_utils.py:

    The review requested replacing an explicit None/len check like:
        if((dataset_features is not None) and (len(dataset_features) > 0)):

    with the more Pythonic truthiness check:
        if dataset_features and (len(dataset_features) > 0):
    """
    source = open("/workspace/tools/distpartitioning/dataset_utils.py", "r", encoding="utf-8").read()

    # Focus on the edge_data block to avoid failing due to unrelated node_data logic.
    edge_data_anchor = "dataset_features = schema_map[constants.STR_EDGE_DATA]"
    assert edge_data_anchor in source, (
        "Expected dataset_utils.py to define dataset_features from schema_map[constants.STR_EDGE_DATA]. "
        "The file structure may have changed unexpectedly."
    )

    # Extract a small window after the edge_data anchor to find the relevant if-statement.
    start = source.index(edge_data_anchor)
    window = source[start : start + 800]

    old_pattern = r"if\s*\(\(\s*dataset_features\s+is\s+not\s+None\s*\)\s*and\s*\(\s*len\s*\(\s*dataset_features\s*\)\s*>\s*0\s*\)\s*\)\s*:"
    new_pattern = r"if\s+dataset_features\s+and\s*\(\s*len\s*\(\s*dataset_features\s*\)\s*>\s*0\s*\)\s*:"

    assert not re.search(old_pattern, window), (
        "Style check failed: edge feature reading still uses the explicit None-check pattern "
        "`if((dataset_features is not None) and (len(dataset_features) > 0)):`. "
        "Expected it to be replaced with a truthiness check."
    )
    assert re.search(new_pattern, window), (
        "Style check failed: expected the edge feature reading guard to use the Pythonic truthiness check "
        "`if dataset_features and (len(dataset_features) > 0):` near the edge_data section."
    )