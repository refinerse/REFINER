import re


def test_macos_warning_uses_10_15_not_1_15():
    source = open("/workspace/sky/setup_files/setup.py", "r", encoding="utf-8").read()

    # The review comment is about the warning message saying ">=1.15" vs ">=10.15".
    # This is not reliably observable at runtime because importing this setup module
    # triggers setuptools CLI behavior; so we validate the literal message in source.
    assert ">=1.15" not in source, (
        "setup.py should not reference a MacOS minimum version of '>=1.15' "
        "in the warning message; it should be '>=10.15'."
    )

    assert re.search(r">=\s*10\.15", source), (
        "setup.py should reference MacOS minimum version '>=10.15' "
        "(e.g., in the warning message for Ray installation requirements)."
    )