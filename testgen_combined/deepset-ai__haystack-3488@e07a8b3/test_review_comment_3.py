import re


def test_parsr_converter_avoids_one_liner_defaulting_assignments():
    """
    Structural style check: ensure the convert() method uses the multi-line
    `if x is None: x = ...` form (more readable, avoids long one-liners).
    """
    source = open("/workspace/haystack/nodes/file_converter/parsr.py", "r", encoding="utf-8").read()

    # The "before" version introduced these one-liners; the "after" version reverted them.
    one_liner_patterns = [
        r"\bvalid_languages\s*=\s*valid_languages\s*if\s*valid_languages\s*is\s*not\s*None\s*else\s*self\.valid_languages\b",
        r"\bid_hash_keys\s*=\s*id_hash_keys\s*if\s*id_hash_keys\s*is\s*not\s*None\s*else\s*self\.id_hash_keys\b",
        r"\bextract_headlines\s*=\s*extract_headlines\s*if\s*extract_headlines\s*is\s*not\s*None\s*else\s*self\.extract_headlines\b",
    ]

    offenders = [pat for pat in one_liner_patterns if re.search(pat, source)]
    assert not offenders, (
        "ParsrConverter.convert() should not use single-line conditional assignments for defaulting "
        "optional params (readability/line length). Found one-liner pattern(s):\n- "
        + "\n- ".join(offenders)
    )

    # Ensure the preferred multi-line style exists for extract_headlines in convert().
    assert (
        "if extract_headlines is None:\n            extract_headlines = self.extract_headlines" in source
    ), "Expected multi-line defaulting for extract_headlines in ParsrConverter.convert()."