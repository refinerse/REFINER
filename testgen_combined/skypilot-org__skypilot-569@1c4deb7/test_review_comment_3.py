import re


def test_installation_doc_macos_requirement_is_precise():
    path = "/workspace/docs/source/getting-started/installation.rst"
    source = open(path, "r", encoding="utf-8").read()

    # The review requested replacing vague wording ("is currently limited", "which works for")
    # with a precise requirement sentence.
    expected_sentence = "For Macs, macOS >= 10.15 is required to install Sky."
    assert expected_sentence in source, (
        "installation.rst should state a precise macOS requirement for installing Sky. "
        f"Expected to find:\n  {expected_sentence}\n"
        "This ensures vague wording was replaced per the review comment."
    )

    # Guard against the old, imprecise note.
    assert "is currently limited" not in source, (
        "installation.rst should not contain the old vague phrasing "
        '"is currently limited" in the macOS note.'
    )
    assert "which works for" not in source, (
        "installation.rst should not contain the old vague phrasing "
        '"which works for" in the macOS note.'
    )

    # Ensure the doc is actually referring to the correct OS version format (10.15),
    # not the incorrect '1.15' used previously.
    assert not re.search(r"macOS\s*version\s*<\s*1\.15", source), (
        "installation.rst should not refer to 'macOS version < 1.15'; "
        "it should use macOS 10.15 as the minimum requirement."
    )