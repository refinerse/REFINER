import os
import re


def test_parser_tests_file_removed_or_no_longer_uses_self_assignment():
    # The merged ("after") version removes this test file entirely (empty file in diff),
    # so the correct behavior is that the old path no longer exists.
    source_path = "/workspace/keep/parser/tests_for_parser/test_parser.py"

    if not os.path.exists(source_path):
        assert True
        return

    # If the file still exists in some environments, enforce the style review comment:
    # do not use `self = Parser()` in free functions; prefer `parser = Parser()`.
    source = open(source_path, "r", encoding="utf-8").read()

    assert "self = Parser()" not in source, (
        "Style: do not assign a Parser instance to a variable named 'self' in a free "
        "function test. Use a descriptive name like `parser = Parser()`."
    )
    assert re.search(r"^\s*parser\s*=\s*Parser\(\)\s*$", source, flags=re.MULTILINE), (
        "Expected `parser = Parser()` instantiation per the review comment, but it was not found."
    )