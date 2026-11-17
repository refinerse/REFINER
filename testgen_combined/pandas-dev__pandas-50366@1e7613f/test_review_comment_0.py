def test_array_to_datetime_error_message_no_search_or_match_suffix():
    """
    The review comment requests unifying the ValueError message to *not* include
    the "(search)" / "(match)" suffix.

    We cannot import the extension module in this environment, so verify via
    source inspection that the formatting suffix was removed.
    """
    source = open("/workspace/pandas/_libs/tslib.pyx", encoding="utf-8").read()

    # Before-version adds helper and appends `({match_msg})` to the error string.
    # After-version removes both.
    assert 'match_msg = "match" if exact else "search"' not in source, (
        "tslib.pyx still defines match_msg used to append '(match)'/'(search)' to the "
        "ValueError message; expected this logic to be removed."
    )
    assert "({match_msg})" not in source, (
        "tslib.pyx still appends '({match_msg})' to the ValueError message; "
        "expected unified message without the suffix."
    )

    # Ensure the ValueError path still exists and uses the unified message.
    expected_snippet = (
        'raise ValueError(\n'
        '                                f"time data \\"{val}\\" at position {i} doesn\'t "\n'
        '                                f"match format \\"{format}\\""\n'
        "                            )"
    )
    assert expected_snippet in source, (
        "Expected the unified ValueError message without '(search)'/'(match)' suffix "
        "to be present in /workspace/pandas/_libs/tslib.pyx."
    )