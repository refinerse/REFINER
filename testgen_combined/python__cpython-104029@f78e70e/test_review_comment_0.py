import re


def test_intrinsic_2_does_not_hardcode_full_disassembly_block():
    """
    Style regression test for Lib/test/test_dis.py:

    Ensure test_intrinsic_2 no longer hardcodes a large disassembly string
    (dis_intrinsic_2_1 + do_disassembly_test), and instead only asserts the
    presence of the specific CALL_INTRINSIC_2 line via assertIn(...get_disassembly...).
    """
    source = open("/workspace/Lib/test/test_dis.py", encoding="utf-8").read()

    # Before: a big triple-quoted expected disassembly block was added.
    assert (
        "dis_intrinsic_2_1" not in source
    ), "Expected no hardcoded disassembly block 'dis_intrinsic_2_1'; test_intrinsic_2 should not require updating large bytecode strings."

    # After: test_intrinsic_2 should just check that a single line is present.
    assert (
        "def test_intrinsic_2(self):" in source
    ), "Expected DisTests.test_intrinsic_2 to exist in Lib/test/test_dis.py."

    assert (
        'self.assertIn("CALL_INTRINSIC_2         1 (INTRINSIC_PREP_RERAISE_STAR)"' in source
    ), (
        "Expected test_intrinsic_2 to assert only for the single "
        "'CALL_INTRINSIC_2         1 (INTRINSIC_PREP_RERAISE_STAR)' line."
    )

    # Ensure it uses runtime disassembly output, not do_disassembly_test against a big string.
    m = re.search(
        r"def test_intrinsic_2\(self\):(?P<body>(?:\n|.)*?)(?:\n\s*def |\nclass |\Z)",
        source,
    )
    assert m, "Could not locate the body of test_intrinsic_2 for inspection."

    body = m.group("body")
    assert (
        "self.do_disassembly_test(" not in body
    ), "Expected test_intrinsic_2 to avoid do_disassembly_test() with hardcoded expected disassembly text."
    assert (
        "self.get_disassembly(" in body
    ), "Expected test_intrinsic_2 to obtain disassembly via get_disassembly() and search within it."