import re


def test_luks_close_exception_assertion_is_strict():
    source = open("/workspace/test/units/modules/crypto/test_luks_device.py", "r", encoding="utf-8").read()

    # The review comment requests tightening the exception handling assertions from:
    #   assert expected == "exception" or expected is False
    # to:
    #   assert expected == "exception"
    #
    # We verify this specifically for test_luks_close's ValueError handler.

    m = re.search(
        r"def\s+test_luks_close\b.*?(?=^def\s+|^@pytest\.mark\.parametrize|\Z)",
        source,
        flags=re.S | re.M,
    )
    assert m is not None, "Expected to find function definition 'test_luks_close' in the source file."

    block = m.group(0)

    assert "except ValueError:" in block, (
        "Expected test_luks_close to handle ValueError; this test checks the strictness of the "
        "assertion inside that exception handler."
    )

    assert 'assert expected == "exception"' in block, (
        'Expected test_luks_close to contain the strict assertion: assert expected == "exception". '
        "This is the behavior requested by the review comment."
    )

    assert 'assert expected == "exception" or expected is False' not in block, (
        "test_luks_close still contains the old, overly-permissive assertion allowing "
        'expected is False on ValueError; it should be strict and only allow expected == "exception".'
    )