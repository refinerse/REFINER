import re


def test_moment_precision_loss_warning_message_is_actionable():
    source = open("/workspace/scipy/stats/_stats_py.py", "r", encoding="utf-8").read()

    # In the corrected code, the warning message explains the condition:
    # "... This occurs when the data are nearly identical. ..."
    # The message is constructed from multiple string literals, and there may be
    # line breaks between words, so match flexibly and case-insensitively.
    actionable_pattern = re.compile(
        r"this\s+occurs\s+when\s+the\s+data\s+are\s+nearly\s+identical",
        re.IGNORECASE | re.MULTILINE,
    )
    assert actionable_pattern.search(source), (
        "Expected the moment-precision-loss RuntimeWarning message to include an "
        "actionable condition for users ('This occurs when the data are nearly identical.')."
    )

    # The corrected spelling is "catastrophic cancellation" (before had 'catastrophc').
    assert re.search(r"catastrophic\s+cancellation", source, re.IGNORECASE), (
        "Expected the moment-precision-loss warning message to contain the corrected phrase "
        "'catastrophic cancellation'."
    )
    assert "catastrophc cancellation" not in source, (
        "Found the old misspelled warning text 'catastrophc cancellation' in the source; "
        "it should have been replaced."
    )