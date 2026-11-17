def test_display_cows_whitelist_guard_includes_none_check():
    """
    The reviewed change is specifically:
        if any(C.ANSIBLE_COW_WHITELIST):
    became:
        if C.ANSIBLE_COW_WHITELIST and any(C.ANSIBLE_COW_WHITELIST):

    This test asserts that the source contains the additional guard, which prevents
    calling any() on None (or other falsey non-iterables).
    """
    source = open("/workspace/lib/ansible/utils/display.py", "r", encoding="utf-8").read()

    assert "if C.ANSIBLE_COW_WHITELIST and any(C.ANSIBLE_COW_WHITELIST):" in source, (
        "Display cowsay whitelist check must guard `any(C.ANSIBLE_COW_WHITELIST)` with a prior "
        "truthiness check (`C.ANSIBLE_COW_WHITELIST and ...`) to avoid errors with None/falsey values. "
        "Expected the updated condition to be present in /workspace/lib/ansible/utils/display.py."
    )