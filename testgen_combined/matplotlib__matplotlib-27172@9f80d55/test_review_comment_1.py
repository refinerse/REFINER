import re


def test_axes_legend_docstring_mentions_empty_legend_drawn():
    """
    Regression test for legend() docstring: calling Axes.legend() with no
    explicit labels emits a UserWarning but still draws an empty legend (tiny
    box). The docstring should reflect that.
    """
    source = open("/workspace/lib/matplotlib/axes/_axes.py", encoding="utf-8").read()

    # Ensure we are checking the right docstring (inside Axes.legend()).
    assert "def legend(self, *args, **kwargs):" in source, (
        "Expected Axes.legend() definition to exist in /workspace/lib/matplotlib/axes/_axes.py"
    )

    # The reviewed change is specifically the wording in the docstring note.
    # Before: "... and no legend being drawn."
    # After:  "... and an empty legend being drawn."
    expected_phrase = "and an empty legend being drawn."
    forbidden_phrase = "and no legend being drawn."

    assert expected_phrase in source, (
        "Axes.legend() docstring should state that, when no labels are set, a "
        "UserWarning is emitted and an empty legend is drawn (tiny box). "
        f"Expected to find {expected_phrase!r} in source."
    )
    assert forbidden_phrase not in source, (
        "Axes.legend() docstring should not claim that 'no legend is drawn' in "
        "the no-labels case; Matplotlib creates/draws an empty legend. "
        f"Unexpectedly found {forbidden_phrase!r} in source."
    )

    # Extra guard: ensure the phrase appears in the relevant note block (not
    # elsewhere in the file).
    note_block_re = re.compile(
        r"\.\. note::\s+"
        r"(?:(?:\n|\r\n)\s+.*?)+?"
        r"without setting the labels manually will result in a ``UserWarning``\s+"
        r"and an empty legend being drawn\.",
        re.MULTILINE,
    )
    assert note_block_re.search(source), (
        "Could not locate the updated '.. note::' block in Axes.legend() "
        "docstring containing the 'empty legend being drawn' wording."
    )