import re


def test_datetime_compare_operation_does_not_wrap_with_isTrue():
    source = open("/workspace/reflex/vars/datetime.py", "r", encoding="utf-8").read()

    assert (
        "def date_compare_operation" in source
    ), "Sanity check: expected date_compare_operation to exist in /workspace/reflex/vars/datetime.py"

    # The review comment requests removing isTrue(...) wrapping for a strictly boolean expression.
    # Before: f"isTrue({lhs} ... {rhs})"
    # After:  f"({lhs} ... {rhs})"
    assert (
        "isTrue(" not in source
    ), "date_compare_operation should not wrap the boolean comparison in isTrue(...); it should return the comparison expression directly."

    # Ensure we still generate a parenthesized comparison expression in the f-string.
    # This guards against accidentally removing the expression entirely or changing it to something unrelated.
    assert re.search(
        r'return\s+var_operation_return\(\s*\n\s*f"\(\{lhs\}\s*\{[^}]*\}\s*\{rhs\}\)"',
        source,
        flags=re.MULTILINE,
    ), (
        "date_compare_operation should build a parenthesized comparison expression like "
        'f"({lhs} { "<" if strict else "<="} {rhs})" passed to var_operation_return.'
    )