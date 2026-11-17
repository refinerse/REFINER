import re


def test_objectexplorer_style_before_section_close_paren_newline():
    path = "/workspace/spyder/plugins/variableexplorer/widgets/objectexplorer/objectexplorer.py"
    source = open(path, "r", encoding="utf-8").read()

    # The style change requested: put the closing parenthesis of the multi-line
    # add_item_to_menu call on its own line after the last keyword argument:
    #
    # After (pass):
    #     before_section=ObjectExplorerOptionsMenuSections.Close
    # )
    #
    # Before (fail):
    #     before_section=ObjectExplorerOptionsMenuSections.Close)
    pattern = re.compile(
        r"before_section\s*=\s*ObjectExplorerOptionsMenuSections\.Close"
        r"\s*\n\s*\)",
        re.MULTILINE,
    )

    assert pattern.search(source), (
        "Style regression: expected `before_section=ObjectExplorerOptionsMenuSections.Close` "
        "to be followed by a newline and then a line containing only the closing "
        "parenthesis for the `add_item_to_menu(...)` call."
    )