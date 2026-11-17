import re


def test_parse_uses_max_for_header_list_instead_of_isinstance_list_check():
    source = open("/workspace/pandas/io/excel/_base.py", encoding="utf-8").read()

    # The style change requested in the review comment is to "just take the maximum
    # in that list" (for header when it's a list of row indices), instead of
    # checking `isinstance(..., list)` and using different branches.
    #
    # AFTER: should contain `header_nrows = max(header)` in parse()
    # BEFORE: used `isinstance(get_sheet_data_header, list)` logic.
    assert (
        "header_nrows = max(header)" in source
    ), "Expected parse() to compute header_nrows using max(header) when header is list-like."

    assert (
        "isinstance(get_sheet_data_header, list)" not in source
    ), "Did not expect parse() to use isinstance(get_sheet_data_header, list); style should use max(header) approach."

    # Also ensure the get_sheet_data call is using the new nrows parameters names
    # (header_nrows/skiprows_nrows) rather than passing header/skiprows directly.
    assert re.search(
        r"data\s*=\s*self\.get_sheet_data\(\s*sheet\s*,\s*convert_float\s*,\s*header_nrows\s*,\s*skiprows_nrows\s*,\s*nrows\s*\)",
        source,
        flags=re.MULTILINE,
    ), "Expected get_sheet_data() call to pass header_nrows and skiprows_nrows (style/API after change)."