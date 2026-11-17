import re


def test_prompt_fileselect_external_description_is_human_readable():
    source = open("/workspace/qutebrowser/mainwindow/prompt.py", encoding="utf-8").read()

    # Ensure the allowed-commands entry exists and uses the more human-readable wording.
    assert (
        "('prompt-fileselect-external', \"Launch external file selector\")" in source
    ), (
        "Expected the allowed-commands description for 'prompt-fileselect-external' to be "
        "'Launch external file selector' (more human readable)."
    )

    # Ensure the old wording is not present anymore (would indicate the style fix wasn't applied).
    assert (
        "('prompt-fileselect-external', \"Launch external fileselect\")" not in source
    ), (
        "Found old allowed-commands description 'Launch external fileselect'; expected it to be "
        "updated to 'Launch external file selector'."
    )

    # Extra guard: ensure we only have one description entry for that command to avoid ambiguity.
    occurrences = len(
        re.findall(r"\('prompt-fileselect-external',\s*\"[^\"]+\"\)", source)
    )
    assert occurrences == 1, (
        "Expected exactly one allowed-commands tuple for 'prompt-fileselect-external', "
        f"but found {occurrences}."
    )