import re


def test_objectexplorer_close_section_trailing_comma_style():
    """
    Source-inspection style test.

    Verifies the style fix requested in the review comment: remove the trailing
    comma before the closing parenthesis in the `add_item_to_menu(... section=...)`
    call for the Close section.

    Before (should fail):  section=ObjectExplorerOptionsMenuSections.Close,)
    After (should pass):   section=ObjectExplorerOptionsMenuSections.Close
                           )
    """
    path = "/workspace/spyder/plugins/variableexplorer/widgets/objectexplorer/objectexplorer.py"
    source = open(path, "r", encoding="utf-8").read()

    # This is the exact bad style pattern from the "before" code.
    assert "section=ObjectExplorerOptionsMenuSections.Close,)" not in source, (
        "Style regression detected: found a trailing comma before the closing "
        "parenthesis in the Close section menu insertion:\n"
        "    section=ObjectExplorerOptionsMenuSections.Close,)\n"
        "The style fix should remove that trailing comma."
    )

    # Ensure the call still exists (guards against false positives).
    assert re.search(
        r"self\.add_item_to_menu\(\s*"
        r"item,\s*"
        r"menu=self\.show_cols_submenu,\s*"
        r"section=ObjectExplorerOptionsMenuSections\.Close\b",
        source,
        flags=re.DOTALL,
    ), (
        "Could not find the expected `self.add_item_to_menu(..., "
        "section=ObjectExplorerOptionsMenuSections.Close ...)` call in the file; "
        "the test cannot verify the intended style change."
    )