import re


def test_phi_propagation_skips_mismatch_only_when_typemap_values_known():
    """
    The fix ensures that when a PHI node's incoming values are missing from the
    typemap (typemap.get(...) returns None), the code does NOT treat the PHI as
    mismatched (because all entries may be None). This is implemented by
    guarding the mismatch check with `v[0] is not None`.
    """
    source = open("/workspace/numba/core/untyped_passes.py", "r", encoding="utf-8").read()

    # The key behavioral change is the introduction of the guard:
    #   if v[0] is not None and any([v[0] != vi for vi in v]):
    #
    # Before code lacked the `v[0] is not None and` part.
    expected_pattern = re.compile(
        r"if\s+v\[0\]\s+is\s+not\s+None\s+and\s+any\(\s*\[\s*v\[0\]\s*!=\s*vi\s+for\s+vi\s+in\s+v\s*\]\s*\)\s*:",
        re.MULTILINE,
    )

    assert expected_pattern.search(source), (
        "PHI node propagation should only skip when incoming typemap values are "
        "known and not all equal. Expected a guard `v[0] is not None and ...` "
        "before the mismatch check, to avoid treating all-None typemap lookups "
        "as a mismatch."
    )