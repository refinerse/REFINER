import re


def test_homophily_docstring_examples_include_expected_outputs_and_no_unused_batch():
    source = open("/workspace/torch_geometric/utils/homophily.py", "r", encoding="utf-8").read()

    # Structural intent: the docstring examples should be complete/doctest-ready
    # by including explicit expected numeric outputs after the example calls.
    required_doctest_outputs = [
        ">>> homophily(edge_index, y, method='edge')\n        0.75",
        ">>> homophily(edge_index, y, method='node')\n        0.6000000238418579",
        ">>> homophily(edge_index, y, method='edge_insensitive')\n        0.19999998807907104",
    ]
    for snippet in required_doctest_outputs:
        assert snippet in source, (
            "Expected homophily() docstring 'Examples' to include explicit doctest "
            f"output for snippet:\n{snippet}\n"
            "This ensures the example is complete and not just an unused call."
        )

    # Review comment hints at an unused variable in the example. In the fixed version,
    # the `batch` example line is removed.
    assert ">>> batch = torch.tensor([0, 0, 0, 1, 1])" not in source, (
        "Docstring example should not define `batch` if it is not used; "
        "expected the unused `batch = ...` example line to be removed."
    )

    # Guard against passing due to formatting changes elsewhere: ensure the 'Examples:'
    # section still exists in the docstring.
    assert re.search(r"\n\s*Examples:\n", source), "Expected an 'Examples:' section in the homophily() docstring."