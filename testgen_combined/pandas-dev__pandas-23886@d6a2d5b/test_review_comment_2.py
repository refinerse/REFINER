import re


def test_styler_clear_docstring_reset_has_no_quotes():
    source = open("/workspace/pandas/io/formats/style.py", encoding="utf-8").read()

    # Ensure we are checking the correct function block
    m = re.search(
        r"def clear\(self\):\n(?P<body>(?:[ \t].*\n)+)",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, "Expected to find `def clear(self):` in style.py"

    body = m.group("body")

    # Structural review request: remove quotes around Reset in docstring.
    # Before: "'Reset' the styler, removing any previously applied styles."
    # After:  "Reset the styler, removing any previously applied styles."
    assert (
        "'Reset' the styler" not in body
    ), "Styler.clear docstring should not quote the word Reset (expect `Reset the styler ...`, not `'Reset' the styler ...`)."

    assert (
        "Reset the styler, removing any previously applied styles." in body
    ), "Expected Styler.clear docstring line: `Reset the styler, removing any previously applied styles.`"