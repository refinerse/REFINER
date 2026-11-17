import re


def test_from_frame_non_frame_checks_error_message():
    source = open(
        "/workspace/pandas/tests/indexes/multi/test_constructor.py", encoding="utf-8"
    ).read()

    # We want to ensure the non-DataFrame case for MultiIndex.from_frame
    # asserts the *error message*, not just the exception type.
    #
    # Before code: `with pytest.raises(TypeError): pd.MultiIndex.from_frame([1,2,3,4])`
    # After code:  `with pytest.raises(TypeError, match='Input must be a DataFrame'): ...`
    #
    # Accept either a pytest.raises(..., match=...) check or tm.assert_raises_regex
    # as long as the message "Input must be a DataFrame" is asserted.
    msg = "Input must be a DataFrame"

    has_pytest_match_check = re.search(
        r"pytest\.raises\s*\(\s*TypeError\s*,\s*match\s*=\s*([rubf]*['\"])"
        + re.escape(msg)
        + r"\1\s*\)",
        source,
        flags=re.MULTILINE,
    )
    has_tm_regex_check = re.search(
        r"tm\.assert_raises_regex\s*\(\s*TypeError\s*,\s*([rubf]*['\"])"
        + re.escape(msg)
        + r"\1\s*,",
        source,
        flags=re.MULTILINE,
    )

    assert has_pytest_match_check or has_tm_regex_check, (
        "Expected the from_frame non-DataFrame test to assert the TypeError message "
        "contains 'Input must be a DataFrame' (e.g. via pytest.raises(..., match=...) "
        "or tm.assert_raises_regex)."
    )