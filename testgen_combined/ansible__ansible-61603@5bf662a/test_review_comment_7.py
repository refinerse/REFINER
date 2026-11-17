import re


def test_valueerror_exception_assertion_is_strict():
    """
    The review comment suggests tightening exception handling assertions from:
        assert expected == "exception" or expected is False
    to:
        assert expected == "exception"

    This test enforces that the updated, strict assertion is present (and the
    permissive variant is absent) in the unit test file under review.
    """
    path = "/workspace/test/units/modules/crypto/test_luks_device.py"
    source = open(path, "r", encoding="utf-8").read()

    permissive = 'assert expected == "exception" or expected is False'
    strict = 'assert expected == "exception"'

    assert permissive not in source, (
        f"{path} still contains the permissive exception assertion "
        f"({permissive!r}); it should be tightened per review comment."
    )

    # Ensure the strict assertion exists in an exception handler context
    assert re.search(r"except\s+ValueError\s*:\s*\n\s*assert expected == \"exception\"", source), (
        f"{path} does not contain the strict ValueError handler assertion "
        f"({strict!r}) in an except ValueError block."
    )