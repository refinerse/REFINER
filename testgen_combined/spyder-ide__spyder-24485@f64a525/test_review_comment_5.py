import os

# Prevent pytest from auto-loading external plugins (e.g. pytest-qt), which can
# crash in this environment due to missing system Qt libraries.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


def test_no_blank_line_after_options_menu_creation():
    """
    Regression test for review comment: "No need of this line."

    Specifically, ensure there is NOT an extra blank line immediately after the
    `options_menu = self.create_menu(...)` block in CollectionsEditorWidget.

    Before version: had a blank line between the closing `)` and the next `for`.
    After version: the `for` follows immediately (no blank line).
    """
    path = "/workspace/spyder/widgets/collectionseditor.py"
    source = open(path, encoding="utf-8").read()

    marker = (
        "        options_menu = self.create_menu(\n"
        "            CollectionsEditorMenus.Options,\n"
        "            register=False\n"
        "        )\n"
    )
    idx = source.find(marker)
    assert idx != -1, (
        f"Expected to find the `options_menu = self.create_menu(...)` block in {path}."
    )

    after = source[idx + len(marker):]

    assert not after.startswith("\n"), (
        "Found an unnecessary blank line immediately after the "
        "`options_menu = self.create_menu(...)` block. The review comment "
        "requested removing that extra line."
    )

    # Ensure the next code line is the expected loop (helps keep the test focused
    # on the reviewed hunk and avoids false positives if file changes a lot).
    next_line = after.splitlines()[0]
    assert next_line.startswith("        for item in [self.close_action]:"), (
        "Expected `for item in [self.close_action]:` to immediately follow the "
        "`options_menu` creation block (with no blank line in between). "
        f"Got: {next_line!r}"
    )