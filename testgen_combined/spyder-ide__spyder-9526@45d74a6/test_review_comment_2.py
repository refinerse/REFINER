import re


def test_expected_folding_levels_variable_defined_in_test_file():
    source_path = "/workspace/spyder/plugins/editor/widgets/tests/test_folding.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    # The review comment requires that the test defines a variable named
    # `expected_folding_levels` equal to what was previously called `lines_lvls`.
    assert "expected_folding_levels" in source, (
        "Missing `expected_folding_levels` variable in "
        "/workspace/spyder/plugins/editor/widgets/tests/test_folding.py"
    )

    assert re.search(r"(?m)^\s*expected_folding_levels\s*=\s*\[", source), (
        "`expected_folding_levels` should be defined as a list assignment "
        "(e.g. `expected_folding_levels = [...]`)."
    )

    assert "lines_lvls" not in source, (
        "Old name `lines_lvls` should not remain after the requested change; "
        "the folding levels list should be renamed to `expected_folding_levels`."
    )