import re


def test_subgraph_docstring_subset_dict_style_formatting():
    source = open("/workspace/torch_geometric/data/hetero_data.py").read()

    # Style change requested in review: the example should use spaced tensor
    # elements: torch.tensor([3, 4, 5, 6]) (not torch.tensor([3,4,5,6])).
    assert "torch.tensor([3, 4, 5, 6])" in source, (
        "Expected HeteroData.subgraph docstring example to format tensor "
        "literal with spaces: torch.tensor([3, 4, 5, 6])."
    )

    # Ensure we are actually checking the style issue and not passing if both
    # versions are present somehow.
    assert "torch.tensor([3,4,5,6])" not in source, (
        "Found unspaced tensor literal torch.tensor([3,4,5,6]) in "
        "torch_geometric/data/hetero_data.py; docstring example should use "
        "spaces after commas."
    )