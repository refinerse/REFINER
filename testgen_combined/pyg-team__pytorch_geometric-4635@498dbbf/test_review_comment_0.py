import re


def test_heterodata_subgraph_uses_subset_dict_parameter_name():
    source = open("/workspace/torch_geometric/data/hetero_data.py").read()

    # The style change in the reviewed diff renamed the parameter from
    # `subset` -> `subset_dict` (and updated the docstring accordingly).
    # We verify this via robust source-level regex checks.
    assert re.search(
        r"\n\s*def\s+subgraph\s*\(\s*self\s*,\s*subset_dict\s*:\s*Dict\[\s*NodeType\s*,\s*Tensor\s*\]\s*\)\s*->\s*'HeteroData'\s*:",
        source,
    ), (
        "Expected HeteroData.subgraph signature to use parameter name "
        "`subset_dict: Dict[NodeType, Tensor]` (style change)."
    )

    assert not re.search(
        r"\n\s*def\s+subgraph\s*\(\s*self\s*,\s*subset\s*:\s*Dict\[\s*NodeType\s*,\s*Tensor\s*\]\s*\)\s*->\s*'HeteroData'\s*:",
        source,
    ), (
        "HeteroData.subgraph still uses parameter name `subset`, but the style "
        "change requires renaming it to `subset_dict`."
    )