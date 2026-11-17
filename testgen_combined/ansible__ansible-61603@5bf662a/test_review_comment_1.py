import re


def test_valueerror_handler_does_not_accept_false_expected():
    """
    The review comment requires that when a ValueError is raised in these tests,
    the except block must only accept it when expected == "exception".
    It must NOT accept expected is False.

    We enforce this by asserting the old, too-permissive pattern is absent and
    the corrected strict assertion is present.
    """
    path = "/workspace/test/units/modules/crypto/test_luks_device.py"
    source = open(path, "r", encoding="utf-8").read()

    permissive_patterns = [
        r'assert\s+expected\s*==\s*["\']exception["\']\s*or\s*expected\s+is\s+False',
        r'assert\s+expected\s*is\s+False\s*or\s*expected\s*==\s*["\']exception["\']',
    ]
    for pat in permissive_patterns:
        assert re.search(pat, source) is None, (
            "The test file still accepts ValueError when expected is False. "
            "The except ValueError block must only accept the exception when "
            'expected == "exception" (strict), not when expected is False.'
        )

    assert re.search(r'except\s+ValueError\s*:\s*\n\s*assert\s+expected\s*==\s*["\']exception["\']', source), (
        "Expected to find a strict ValueError handler assertion of the form:\n"
        '    except ValueError:\n        assert expected == "exception"\n'
        "This ensures exceptions are only accepted when explicitly expected."
    )