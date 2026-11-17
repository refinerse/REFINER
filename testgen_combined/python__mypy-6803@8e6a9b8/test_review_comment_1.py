import re


def test_check_subtype_invariance_notes_loop_unconditional():
    """
    Structural regression test for mypy/checker.py:

    The review comment asked to remove a redundant `if notes:` guard before looping:
        if notes:
            for note in notes: ...
    since `for note in notes:` is already a no-op for an empty list.

    This test inspects the source to ensure the redundant guard is absent.
    It should FAIL on the "before" version (guard present) and PASS on the
    "after" version (guard removed).
    """
    source = open("/workspace/mypy/checker.py", "r", encoding="utf-8").read()

    # Narrow to the check_subtype method body to avoid false positives elsewhere.
    m = re.search(r"\n\s+def check_subtype\(", source)
    assert m, "Expected to find 'def check_subtype' in /workspace/mypy/checker.py"

    start = m.start()
    next_def = re.search(r"\n\s+def [a-zA-Z_]+\(", source[m.end():])
    end = (m.end() + next_def.start()) if next_def else len(source)
    chunk = source[start:end]

    # The old redundant pattern we want to ensure is gone.
    redundant_pattern = re.search(r"\n\s+if notes:\n\s+for note in notes:", chunk)
    assert (
        redundant_pattern is None
    ), "Redundant 'if notes:' guard before 'for note in notes:' should be removed; loop already skips empty lists."

    # And the new unconditional loop should exist.
    assert re.search(
        r"\n\s+for note in notes:\n\s+self\.msg\.note\(", chunk
    ), "Expected unconditional 'for note in notes:' loop calling self.msg.note(...) in check_subtype."