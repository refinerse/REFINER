import re


def test_comments8_is_shortened_and_demonstrates_cell_marker_standardization():
    path = "/workspace/tests/data/comments8.py"
    source = open(path, "r", encoding="utf8").read()

    # Review request: shorten the file to focus only on the '#%%' / '# %%' markers.
    assert "def func" not in source, (
        "comments8.py should be shortened to only demonstrate Spyder cell markers; "
        "found 'def func', indicating the old large example is still present."
    )

    # The file should still contain an input and output section.
    assert "\n# output\n" in source, "Expected comments8.py to contain an '# output' section."
    before, after = source.split("\n# output\n", 1)

    # Input section: show both accepted forms.
    assert "#%%" in before, "Expected the input section to include '#%%'."
    assert "# %%" in before, "Expected the input section to include '# %%'."

    # Output section: both markers should appear as '# %%' (but '#%%' may still appear in prose).
    output_marker_lines = re.findall(r"(?m)^#\s*%%\s*$", after)
    assert output_marker_lines, "Expected the output section to contain cell-marker comment lines."

    assert all(line.strip() == "# %%" for line in output_marker_lines), (
        "Expected all output cell-marker lines to be exactly '# %%' (standardized form). "
        f"Got: {output_marker_lines!r}"
    )

    # Specifically, we expect two marker lines in the output section.
    assert len(output_marker_lines) == 2, (
        "Expected exactly two cell-marker lines in the output section (both standardized to '# %%')."
    )