import re


def test_convert_uses_extract_headlines_param_not_self_extract_headlines():
    """
    The review comment asks to use the local `extract_headlines` (the effective setting for this call)
    rather than `self.extract_headlines` when deciding whether to attach headlines to meta.
    """
    source = open("/workspace/haystack/nodes/file_converter/parsr.py", "r", encoding="utf-8").read()

    # Ensure we are checking the right block: within convert(), after the language validation warning.
    # In the fixed version we expect `if extract_headlines:` (not `if self.extract_headlines:`)
    # before setting `meta["headlines"] = headlines`.
    pattern_fixed = r"if\s+extract_headlines\s*:\s*\n\s*meta\[\s*[\"']headlines[\"']\s*\]\s*=\s*headlines"
    pattern_old = r"if\s+self\.extract_headlines\s*:\s*\n(?:\s*meta\s*=\s*meta\s+if\s+meta\s+else\s*\{\}\s*\n)?\s*meta\[\s*[\"']headlines[\"']\s*\]\s*=\s*headlines"

    assert re.search(
        pattern_fixed, source, flags=re.MULTILINE
    ), "Expected ParsrConverter.convert() to gate meta['headlines'] assignment with `if extract_headlines:`."

    assert not re.search(
        pattern_old, source, flags=re.MULTILINE
    ), "ParsrConverter.convert() should not gate meta['headlines'] assignment with `if self.extract_headlines:`; it must use the method's effective `extract_headlines` value."