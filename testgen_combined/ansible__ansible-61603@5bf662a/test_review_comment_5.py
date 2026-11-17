import re


def test_valueerror_exception_assertion_is_strict():
    """
    The review comment requests changing the overly-permissive exception assertion:

        assert expected == "exception" or expected is False

    to the strict form:

        assert expected == "exception"

    in the except ValueError blocks (e.g., in test_luks_close/test_luks_add_key/test_luks_remove_key/etc).

    This test enforces that the file no longer allows `expected is False` in ValueError handlers.
    """
    path = "/workspace/test/units/modules/crypto/test_luks_device.py"
    source = open(path, "r", encoding="utf-8").read()

    # Ensure we still have ValueError exception handling blocks in this file
    assert "except ValueError:" in source, "Expected ValueError handlers to exist in the test file."

    # The "before" version contains permissive assertions allowing expected is False.
    permissive_pattern = r'assert\s+expected\s*==\s*["\']exception["\']\s*or\s*expected\s+is\s+False'
    assert not re.search(permissive_pattern, source), (
        "ValueError handler still contains permissive assertion allowing `expected is False`. "
        "It should be strict: `assert expected == \"exception\"`."
    )

    # The "after" version should contain at least one strict assertion.
    strict_pattern = r'assert\s+expected\s*==\s*["\']exception["\']\s*(?:\n|$)'
    assert re.search(strict_pattern, source), (
        "Expected at least one strict `assert expected == \"exception\"` in a ValueError handler."
    )