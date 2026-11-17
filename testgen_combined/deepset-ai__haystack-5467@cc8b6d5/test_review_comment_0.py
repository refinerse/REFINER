import re


def test_language_validation_uses_single_if_statement():
    source = open("/workspace/haystack/preview/components/file_converters/txt.py", "r", encoding="utf-8").read()

    # The review comment asked to use a single if statement instead of nested:
    # Before (should fail this test):
    #   if data.valid_languages is not None:
    #       if not ..._validate_language(...):
    # After (should pass this test):
    #   if data.valid_languages is not None and not ..._validate_language(...):
    #
    # We enforce presence of the single-if pattern and absence of the nested-if pattern.
    single_if_pattern = r"if\s+data\.valid_languages\s+is\s+not\s+None\s+and\s+not\s+.*_validate_language\s*\("
    nested_if_pattern = r"if\s+data\.valid_languages\s+is\s+not\s+None\s*:\s*\n\s*if\s+not\s+.*_validate_language\s*\("

    assert re.search(
        single_if_pattern, source
    ), "Expected language validation to use a single `if data.valid_languages is not None and not _validate_language(...)`."

    assert not re.search(
        nested_if_pattern, source, flags=re.MULTILINE
    ), "Did not expect nested `if data.valid_languages is not None: if not _validate_language(...)` (extra indentation)."