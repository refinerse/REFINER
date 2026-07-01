import re


def test_no_duplicate_isinstance_assert_in_most_similar_documents_test():
    """
    The review comment points out a duplicated assert:
        assert isinstance(output, list)
        assert isinstance(output, list)

    This test enforces that the duplicated line is not present in /workspace/test/test_pipeline.py.
    """
    source = open("/workspace/test/test_pipeline.py", "r", encoding="utf-8").read()

    # Specifically detect two consecutive identical asserts (allowing whitespace between them).
    duplicate_pattern = re.compile(
        r"assert\s+isinstance\(\s*output\s*,\s*list\s*\)\s*[\r\n]+\s*assert\s+isinstance\(\s*output\s*,\s*list\s*\)",
        re.MULTILINE,
    )

    assert not duplicate_pattern.search(source), (
        "Found duplicated consecutive assertion `assert isinstance(output, list)` in "
        "/workspace/test/test_pipeline.py. The test should contain this assertion only once."
    )