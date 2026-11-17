import re


def test_download_prompt_wait_does_not_match_specific_filename_pattern():
    """Ensure the external fileselector scenario waits for any download prompt ("*")
    rather than a filename-specific pattern ("*/download.bin"), as requested in the review.
    """
    path = "/workspace/tests/end2end/features/downloads.feature"
    source = open(path, encoding="utf-8").read()

    # Find the "Scenario: Select download path" block.
    m = re.search(
        r"(?ms)^[ \t]*Scenario:\s*Select download path\s*\n(.*?)(?=^[ \t]*Scenario:|\Z)",
        source,
    )
    assert m is not None, f"Could not find 'Scenario: Select download path' in {path}"
    block = m.group(1)

    assert (
        'And I wait for the download prompt for "*"\n' in block
    ), (
        "The 'Select download path' scenario should wait for the download prompt for '*', "
        "so the test doesn't depend on downloads.location.suggestion including the filename. "
        "Expected to find: And I wait for the download prompt for \"*\""
    )

    assert (
        'And I wait for the download prompt for "*/download.bin"' not in block
    ), (
        "The 'Select download path' scenario must not wait for a filename-specific prompt "
        "pattern (\"*/download.bin\"), as that can fail when the prompt default is a directory."
    )