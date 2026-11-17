import re


def test_action_yml_uses_pep440_python_version_specifier_language():
    source = open("/workspace/action.yml", "r", encoding="utf-8").read()

    # The review requests the input description to explicitly mention PEP440
    # and provide an example like "21.5b1" (not "==20.8b1"), and the input key
    # was renamed from black_version -> version.
    assert (
        "Python Version specifier (PEP440)" in source
    ), "action.yml should describe the version input as a PEP440 Python version specifier."

    assert re.search(r"^\s+version:\s*$", source, flags=re.MULTILINE), (
        "action.yml should define an input named 'version:' (renamed from 'black_version')."
    )

    assert not re.search(r"^\s+black_version:\s*$", source, flags=re.MULTILINE), (
        "action.yml should no longer define an input named 'black_version:'; it should be 'version:'."
    )

    # Ensure the old example with '==' is not present; the updated description example is "21.5b1".
    assert "==20.8b1" not in source, (
        "action.yml should not suggest a '==20.8b1' example; the input should be a PEP440 specifier "
        'example like "21.5b1".'
    )
    assert "21.5b1" in source, 'action.yml should include the example version "21.5b1" in the description.'