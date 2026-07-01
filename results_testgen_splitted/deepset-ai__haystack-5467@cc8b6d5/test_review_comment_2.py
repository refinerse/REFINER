import re


def test_prepare_metadata_error_message_has_trailing_period():
    """
    The review comment adds a trailing period to the error message when meta length mismatches paths length.
    Verify that the source contains the updated string with a trailing '.'.
    """
    source = open("/workspace/haystack/preview/components/file_converters/txt.py", encoding="utf-8").read()

    # We expect the specific f-string segment to end with a period:
    # ... number of meta entries: {len(meta)}."
    pattern = r'number of meta entries:\s*\{len\(meta\)\}\."\s*\)'
    assert re.search(pattern, source), (
        "Expected PipelineRuntimeError message to include a trailing period after "
        "'number of meta entries: {len(meta)}.' when meta list length mismatches paths length. "
        "This should fail before the review change (missing '.') and pass after."
    )