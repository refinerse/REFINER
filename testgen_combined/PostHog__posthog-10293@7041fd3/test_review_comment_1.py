import re


def test_selected_column_display_item_uses_primary_bg_hover_variable():
    source = open("/workspace/frontend/src/lib/components/ResizableTable/TableConfig.scss").read()

    # Ensure the selected state uses the correct CSS variable.
    assert (
        "background-color: var(--primary-bg-hover);" in source
    ), "Expected '.column-display-item.selected' to use 'background-color: var(--primary-bg-hover);' (not --bg-light-blue)."

    # Ensure we didn't keep the incorrect variable in the selected block.
    # (This makes the failure mode clearer on the 'before' version.)
    selected_blocks = re.findall(r"&\.selected\s*\{[^}]*\}", source, flags=re.DOTALL)
    assert selected_blocks, "Expected to find at least one '&.selected { ... }' block in TableConfig.scss."

    assert all(
        "var(--bg-light-blue)" not in block for block in selected_blocks
    ), "Did not expect 'var(--bg-light-blue)' to be used inside any '&.selected { ... }' block; should use '--primary-bg-hover'."