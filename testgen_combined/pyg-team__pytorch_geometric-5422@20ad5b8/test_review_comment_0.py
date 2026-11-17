import re


def test_from_networkx_examples_comment_is_python_doctest_comment():
    source = open("/workspace/torch_geometric/utils/convert.py", "r", encoding="utf-8").read()

    # The review comment changes a doctest "output-like" line:
    #     >>> A `Data` object is returned
    # into a proper python comment within doctest:
    #     >>> # A `Data` object is returned
    #
    # We assert the corrected line exists, and the incorrect one does not.
    assert ">>> # A `Data` object is returned" in source, (
        "Expected from_networkx() docstring example to contain a valid doctest "
        "comment line '>>> # A `Data` object is returned' (per review)."
    )

    # Ensure we don't still have the invalid doctest line (without '#') anywhere.
    # Use a regex to match the exact prompt followed by the text, not already commented.
    assert re.search(r"(?m)^\s*>>>\s+A `Data` object is returned\s*$", source) is None, (
        "Found an invalid doctest line '>>> A `Data` object is returned' without "
        "a leading '#'. This should have been changed to a comment."
    )