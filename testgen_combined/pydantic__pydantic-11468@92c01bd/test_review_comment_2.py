import re


def test_usage_errors_validate_by_alias_and_name_section_not_model_specific():
    source = open("/workspace/docs/errors/usage_errors.md", encoding="utf-8").read()

    anchor = "{#validate-by-alias-and-name-false}"
    idx = source.find(anchor)
    assert idx != -1, f"Expected to find the validate-by-alias-and-name-false section anchor {anchor!r} in usage_errors.md"

    # Extract the paragraph immediately following the heading (up to the next blank line)
    after_anchor = source[idx:]
    m = re.search(r"\n\n([^\n]+)\n\n", after_anchor)
    assert m, "Expected to find a paragraph immediately after the validate-by-alias-and-name-false heading"
    paragraph = m.group(1).strip()

    assert "model's configuration" not in paragraph, (
        "Docs for this error should not describe it as specific to a model's configuration; "
        "it should refer to configuration in general (e.g. TypeAdapter/dataclass/BaseModel config). "
        f"Found paragraph: {paragraph!r}"
    )
    assert "in the configuration" in paragraph, (
        "Expected the paragraph to describe the error as raised when validate_by_alias and validate_by_name "
        "are both False in the configuration (general), not model-specific. "
        f"Found paragraph: {paragraph!r}"
    )