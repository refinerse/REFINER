import re


def test_preprocessor_max_chars_docstring_spelling_and_char_unit():
    source = open("/workspace/haystack/nodes/preprocessor/preprocessor.py", "r", encoding="utf-8").read()

    # Ensure we're checking the right docstring line and that it includes the unit "in characters".
    # BEFORE: "maximum lenght ... longer than max_chars after pre-processing ..."
    # AFTER:  "maximum length ... longer than max_chars_check in characters after pre-processing ..."
    docstring_param_lines = re.findall(r"^\s*:param\s+max_chars(?:_check)?\s*:(.*)$", source, flags=re.MULTILINE)
    assert docstring_param_lines, "Expected a ':param max_chars...' (or ':param max_chars_check...') line in the docstring."

    combined = " ".join(line.strip() for line in docstring_param_lines)

    assert "maximum length" in combined, (
        "The docstring should use correct spelling 'length' (not 'lenght') for the max_chars parameter description."
    )
    assert "maximum lenght" not in combined, (
        "Found misspelled 'lenght' in the max_chars parameter docstring; it should be 'length'."
    )
    assert "in characters" in combined, (
        "The docstring should explicitly specify the unit: the maximum length is 'in characters'."
    )