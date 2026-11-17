import re


def test_texteditor_toolbar_loop_style_inline_list():
    source = open(
        "/workspace/spyder/plugins/variableexplorer/widgets/texteditor.py",
        "r",
        encoding="utf-8",
    ).read()

    # After the review, the loop was reformatted to a single-line list literal:
    #     for item in [stretcher, options_button]:
    expected = "for item in [stretcher, options_button]:"
    assert expected in source, (
        "Expected the toolbar items loop to use a single-line list literal:\n"
        "    for item in [stretcher, options_button]:\n"
        "This is the style change requested in the review comment."
    )

    # Before the review, it used a multi-line list literal. Ensure it's gone.
    old_pattern = re.compile(
        r"for item in\s*\[\s*\n\s*stretcher\s*,\s*\n\s*options_button\s*\n\s*\]\s*:",
        re.MULTILINE,
    )
    assert not old_pattern.search(source), (
        "Found the old multi-line list literal form:\n"
        "    for item in [\n"
        "        stretcher,\n"
        "        options_button\n"
        "    ]:\n"
        "Expected it to be replaced by a single-line list literal."
    )