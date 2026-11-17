import re


def test_excel_base_parse_header_skiprows_nrows_style_conversion():
    source = open("/workspace/pandas/io/excel/_base.py", encoding="utf-8").read()

    # The addressed review change replaces the old "0 if header is None else header"
    # style with an explicit isinstance(header, int) / header is None / else block.
    assert (
        "get_sheet_data_header = 0 if header is None else header" not in source
    ), (
        "Expected the old ternary assignment for get_sheet_data_header to be removed. "
        "Found: 'get_sheet_data_header = 0 if header is None else header'."
    )

    assert (
        "if isinstance(header, int):" in source
        and "elif header is None:" in source
        and "else:" in source
        and "header_nrows" in source
    ), (
        "Expected explicit header->header_nrows conversion logic in BaseExcelReader.parse, "
        "using an isinstance(header, int) / header is None / else structure assigning "
        "to 'header_nrows'."
    )

    # Also ensure that parse now passes header_nrows/skiprows_nrows into get_sheet_data.
    assert re.search(
        r"data\s*=\s*self\.get_sheet_data\(\s*sheet\s*,\s*convert_float\s*,\s*header_nrows\s*,\s*skiprows_nrows\s*,\s*nrows\s*\)",
        source,
    ), (
        "Expected BaseExcelReader.parse to call get_sheet_data(sheet, convert_float, "
        "header_nrows, skiprows_nrows, nrows)."
    )