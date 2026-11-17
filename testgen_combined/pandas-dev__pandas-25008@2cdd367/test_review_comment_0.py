def test_validate_docstrings_uses_ast_based_return_detection_not_regex():
    source = open("/workspace/scripts/validate_docstrings.py", encoding="utf-8").read()

    # After: return detection should be AST-based (method_returns_something property)
    assert "def method_returns_something" in source, (
        "Expected an AST-based helper `method_returns_something` to exist in "
        "scripts/validate_docstrings.py (added in the reviewed change)."
    )

    # After: get_validation_data should consult the helper instead of searching via regex
    assert "if doc.method_returns_something:" in source, (
        "Expected get_validation_data to use `doc.method_returns_something` to "
        "decide whether RT01 should be raised when Returns section is missing."
    )

    # Before: the RT01 check used a verbose regex that looked for a return statement
    assert "re.search(r\"\"\" \\\"\\\"\\\".*\\\"\\\"\\\".*  # Skip the docstring." not in source, (
        "Found the old regex-based return detection still present. The reviewed "
        "change should remove this regex in favor of AST-based detection."
    )