import re


def test_xlrd_get_sheet_data_does_not_append_empty_rows_when_skipping():
    """
    Regression test for review comment: avoid appending empty lists for skipped rows.
    We can't import pandas in this environment, so we inspect the source.
    """
    source = open("/workspace/pandas/io/excel/_xlrd.py", encoding="utf-8").read()

    # Before version appended [] when skipping a row:
    #   if self.should_skip_row(...):
    #       data.append([])
    #       continue
    #
    # After version removed should_skip_row usage entirely and does not append [].
    pattern = re.compile(
        r"if\s+self\.should_skip_row\([^\)]*\)\s*:\s*\n\s*data\.append\(\[\]\)",
        re.MULTILINE,
    )

    assert not pattern.search(source), (
        "get_sheet_data should not append an empty list for skipped rows; "
        "skipping rows should be done by not reading/appending them at all. "
        "Found 'if self.should_skip_row(...): data.append([])' pattern in _xlrd.py."
    )