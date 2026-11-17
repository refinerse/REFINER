import re


def test_register_shortcut_for_widget_style_multiline_close_call():
    """
    Verify the style change requested in the review: the call to
    register_shortcut_for_widget for the 'close' shortcut is formatted as a
    multiline call with the closing parenthesis on its own line.
    """
    source = open(
        "/workspace/spyder/widgets/collectionseditor.py", encoding="utf-8"
    ).read()

    # Sanity check: ensure the call exists at all.
    assert "register_shortcut_for_widget" in source, (
        "Expected a call to register_shortcut_for_widget in "
        "/workspace/spyder/widgets/collectionseditor.py."
    )

    # The reviewed style expects:
    # self.register_shortcut_for_widget(
    #     name='close', triggered=self.close_window
    # )
    # (allowing either quote type and arbitrary indentation)
    multiline_pattern = re.compile(
        r"self\.register_shortcut_for_widget\(\s*"
        r"\n\s*name\s*=\s*['\"]close['\"]\s*,\s*triggered\s*=\s*self\.close_window\s*"
        r"\n\s*\)",
        re.MULTILINE,
    )

    assert multiline_pattern.search(source), (
        "Expected register_shortcut_for_widget to be formatted as a multiline "
        "call with the closing parenthesis on its own line, e.g.:\n"
        "    self.register_shortcut_for_widget(\n"
        "        name='close', triggered=self.close_window\n"
        "    )\n"
        "The current source does not match this style."
    )