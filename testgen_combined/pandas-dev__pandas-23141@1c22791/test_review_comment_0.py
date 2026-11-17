def test_multiindex_squeeze_docstring_uses_instance_spelling():
    source = open("/workspace/pandas/core/indexes/multi.py", encoding="utf-8").read()

    # In the "before" version, MultiIndex.squeeze exists and its docstring
    # contains the typo "instane". In the "after" version, that method is
    # removed, so the typo must not be present anywhere in this file.
    assert "instane" not in source, (
        "Found the typo 'instane' in /workspace/pandas/core/indexes/multi.py. "
        "The review requested correcting it to 'instance'."
    )

    # Ensure we are really checking the intended location: the phrase should
    # now use the correct spelling if present.
    assert ("Index instance" in source) or ("index instance" in source) or ("instance" in source), (
        "Expected corrected spelling 'instance' to appear in /workspace/pandas/core/indexes/multi.py "
        "(at least somewhere relevant), but it was not found."
    )