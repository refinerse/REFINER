def test_multi_py_does_not_contain_misspelling_multiiindex_and_mentions_multiindex():
    source = open("/workspace/pandas/core/indexes/multi.py", encoding="utf-8").read()
    lower = source.lower()

    assert "multiiindex" not in lower, (
        "The source contains the misspelling 'multiiindex' (case-insensitive). "
        "It should be 'MultiIndex'."
    )

    # Sanity check that we're looking at the expected module content.
    assert "class multiindex" in lower, (
        "Expected MultiIndex class definition in pandas/core/indexes/multi.py."
    )