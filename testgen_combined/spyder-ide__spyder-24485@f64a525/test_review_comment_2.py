import os
import re


def test_toolbar_create_toolbar_call_is_pep8_indented():
    # Prevent pytest from auto-loading external plugins (e.g. pytest-qt), which
    # can crash in this container due to missing system Qt libs.
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    path = "/workspace/spyder/plugins/variableexplorer/widgets/texteditor.py"
    source = open(path, encoding="utf-8").read()

    # The style change requested in the review was to fix indentation of this call:
    #
    # self.toolbar = self.create_toolbar(
    #     TextEditorWidgets.Toolbar,
    #     register=False
    # )
    #
    # Before: args were indented too far and closing paren misaligned.
    bad_style = re.compile(
        r"self\.toolbar\s*=\s*self\.create_toolbar\(\n"
        r"\s{16}TextEditorWidgets\.Toolbar,\n"
        r"\s{16}register=False\n"
        r"\s{12}\)",
        re.MULTILINE,
    )
    assert not bad_style.search(source), (
        "Found the old, over-indented `self.create_toolbar(...)` call. "
        "Expected arguments and closing parenthesis to be aligned with a "
        "standard 4-space continuation indent."
    )

    good_style = re.compile(
        r"self\.toolbar\s*=\s*self\.create_toolbar\(\n"
        r"\s{8}TextEditorWidgets\.Toolbar,\n"
        r"\s{8}register=False\n"
        r"\s{8}\)",
        re.MULTILINE,
    )
    assert good_style.search(source), (
        "Could not find the expected PEP8-style indentation for "
        "`self.toolbar = self.create_toolbar(...)`:\n"
        "    self.toolbar = self.create_toolbar(\n"
        "        TextEditorWidgets.Toolbar,\n"
        "        register=False\n"
        "    )"
    )