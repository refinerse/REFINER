import re


def test_subgraph_uses_is_node_attr_and_is_edge_attr_in_loops():
    source = open("/workspace/torch_geometric/data/hetero_data.py", "r").read()

    # Extract the `subgraph` method body.
    # Match either:
    #   def subgraph(... ) -> 'HeteroData':
    # or any other return annotation / formatting.
    m = re.search(
        r"\n\s+def\s+subgraph\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:(?P<body>.*?)(?=\n\s+def\s|\n# Helper functions)",
        source,
        flags=re.S,
    )
    assert m is not None, "Expected HeteroData.subgraph method to exist."

    body = m.group("body")

    assert "is_node_attr(" in body, (
        "HeteroData.subgraph should use NodeStorage.is_node_attr(key) to decide "
        "which node attributes to index by the subset (style simplification)."
    )
    assert "is_edge_attr(" in body, (
        "HeteroData.subgraph should use EdgeStorage.is_edge_attr(key) to decide "
        "which edge attributes to mask by edge_mask (style simplification)."
    )

    assert "value.shape[0] == cur_num_nodes" not in body, (
        "HeteroData.subgraph should not rely on `value.shape[0] == cur_num_nodes` "
        "to detect node attributes; it should use is_node_attr/is_edge_attr."
    )