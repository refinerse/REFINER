import re


def test_choose_file_docstring_mentions_up_downloading_and_external_command():
    """The choose_file docstring should mention up-/downloading and an external command."""
    source = open("/workspace/qutebrowser/browser/shared.py", encoding="utf-8").read()

    # Extract the first (summary) line of choose_file's docstring.
    m = re.search(
        r"def choose_file\([^)]*\)\s*->\s*List\[str\]:\s*\n\s*\"\"\"([^\n]*)",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, "Could not locate choose_file docstring in /workspace/qutebrowser/browser/shared.py"
    summary_line = m.group(1).strip()

    expected = "Select file(s)/folder for up-/downloading, using an external command."
    assert summary_line == expected, (
        "choose_file docstring summary line should be updated to reflect selection for "
        "up-/downloading and mention 'an external command' exactly.\n"
        f"Expected: {expected!r}\n"
        f"Got:      {summary_line!r}"
    )