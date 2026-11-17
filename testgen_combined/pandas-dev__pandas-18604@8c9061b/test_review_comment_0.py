import re


def test_read_excel_does_not_raise_for_sheetname_when_sheet_name_provided():
    """
    Regression test for the behavior change in pandas/io/excel.py:

    * Before: if sheet_name is provided positionally (default 0) AND the caller
      passes sheetname=..., the code raised TypeError (treated as specifying
      both sheet_name and sheetname).
    * After: in this scenario, sheetname should be accepted (deprecated) and
      used, not raising TypeError.

    We cannot import pandas here, so we verify the changed control-flow via
    source inspection of /workspace/pandas/io/excel.py.
    """
    source = open("/workspace/pandas/io/excel.py", encoding="utf-8").read()

    # In the corrected ("after") code, the special-case deprecation branch
    # pops sheetname, and there is NO subsequent `elif 'sheetname' in kwds:`
    # in read_excel that raises TypeError.
    #
    # In the buggy ("before") code, there *is* an `elif 'sheetname' in kwds:`
    # branch in read_excel which raises TypeError.
    m = re.search(r"def\s+read_excel\s*\(", source)
    assert m, "Could not find read_excel definition in /workspace/pandas/io/excel.py"

    # Grab a limited slice after the definition to keep the regex checks focused.
    read_excel_block = source[m.start() : m.start() + 4000]

    assert "kwds.pop(\"sheetname\")" in read_excel_block or "kwds.pop('sheetname')" in read_excel_block, (
        "Expected read_excel to pop the deprecated 'sheetname' kwarg when "
        "sheet_name is left at its default (0), instead of treating it as a "
        "conflicting specification."
    )

    assert "Cannot specify both `sheet_name` and `sheetname`" not in read_excel_block, (
        "read_excel still appears to reject `sheetname` as conflicting with the "
        "default sheet_name=0; after the fix, this conflict should not be raised "
        "in read_excel for the default sheet_name case."
    )

    # Ensure the new unexpected-keyword guard for 'sheet' is present (as per diff).
    assert re.search(r"if\s+['\"]sheet['\"]\s+in\s+kwds\s*:\s*\n\s*raise\s+TypeError\(", read_excel_block), (
        "Expected read_excel to explicitly raise TypeError for unexpected "
        "keyword argument 'sheet'."
    )