import re


def test_setup_py_warn_message_is_quoted_and_mentions_correct_versions():
    source = open("/workspace/sky/setup_files/setup.py", "r", encoding="utf-8").read()

    # The review comment asks for quotes around "to install ray>=1.9".
    # The addressed version wraps the warning message itself in escaped quotes:
    #   f"\'Detected ... install ray>=1.9\'"
    # The before version has no such surrounding quotes and also contains typos
    # like >=1.15 / "satisfy Ray>=1.9".
    assert "\\'Detected MacOS version" in source, (
        "Expected the MacOS/Ray warning string to start with an escaped single "
        "quote (\\'Detected...), indicating the message is quoted as requested."
    )

    assert ">=10.15" in source, (
        "Expected the warning message to reference MacOS >=10.15 (not >=1.15)."
    )

    assert "install ray>=1.9" in source, (
        "Expected the warning message to say 'install ray>=1.9' (lowercase ray), "
        "matching the style request."
    )

    # Ensure the message is actually closed with an escaped trailing quote.
    assert "ray>=1.9\\'" in source, (
        "Expected the warning message to end with an escaped single quote after "
        "'ray>=1.9', indicating the full warning is quoted."
    )