import re


def test_read_json_new_args_are_typed_and_nrows_documented_once():
    source = open("/workspace/pandas/io/json/_json.py", encoding="utf-8").read()

    # --- Signature typing checks (requested in review comment) ---
    # Before: lines=False, chunksize=None, nrows=None (no annotations)
    # After:  lines: bool = False, chunksize: Optional[int] = None, nrows: Optional[int] = None
    assert "lines: bool = False" in source, (
        "Expected read_json signature to type-annotate the new/existing arg "
        "'lines' as `lines: bool = False`."
    )
    assert "chunksize: Optional[int] = None" in source, (
        "Expected read_json signature to type-annotate the new/existing arg "
        "'chunksize' as `chunksize: Optional[int] = None`."
    )
    assert "nrows: Optional[int] = None" in source, (
        "Expected read_json signature to type-annotate the new arg "
        "'nrows' as `nrows: Optional[int] = None`."
    )

    # --- Documentation check: avoid duplicated 'chunksize' parameter block and add 'nrows' docs ---
    # In the before version, docstring incorrectly has TWO "chunksize : int, optional" blocks.
    chunksize_doc_header_count = len(re.findall(r"(?m)^\s*chunksize\s*:\s*int,\s*optional\s*$", source))
    assert chunksize_doc_header_count == 1, (
        "Expected read_json docstring to document 'chunksize' exactly once; "
        f"found {chunksize_doc_header_count} 'chunksize : int, optional' blocks."
    )

    # Ensure 'nrows' has a proper parameter doc block with a versionadded directive.
    assert re.search(r"(?m)^\s*nrows\s*:\s*int,\s*optional\s*$", source), (
        "Expected read_json docstring to include a parameter section header "
        "for `nrows : int, optional`."
    )
    assert re.search(r"(?m)^\s*\.\.\s*versionadded::\s*1\.1\b", source), (
        "Expected read_json docstring to include `.. versionadded:: 1.1` for the new `nrows` parameter."
    )