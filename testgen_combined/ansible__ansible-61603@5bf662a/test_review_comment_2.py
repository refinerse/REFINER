import re


def test_valueerror_handler_only_accepts_exception_expected():
    """
    The review comment changes the exception handler assertions from:
        assert expected == "exception" or expected is False
    to:
        assert expected == "exception"

    Verify the updated, stricter assertion is present (and the old permissive one is not).
    """
    source = open("/workspace/test/units/modules/crypto/test_luks_device.py", "r", encoding="utf-8").read()

    # New behavior requested by review comment: only "exception" is acceptable on ValueError.
    assert 'assert expected == "exception"' in source, (
        'Expected the stricter exception-path assertion `assert expected == "exception"` '
        "to be present in /workspace/test/units/modules/crypto/test_luks_device.py."
    )

    # Old behavior (before) allowed `expected is False` as well; ensure it's gone.
    assert re.search(r'assert\s+expected\s*==\s*"exception"\s+or\s+expected\s+is\s+False', source) is None, (
        "Found the old permissive assertion allowing `expected is False` in the ValueError handler. "
        "The updated code should only accept `expected == \"exception\"`."
    )