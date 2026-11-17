import re


def test_pipeline_extractive_qa_authentication_tests_removed_after_review():
    """
    The review discussion concluded that the newly added "authentication/headers" tests were overly expansive
    and redundant, and the merged version removes them.

    This test verifies that /workspace/test/test_pipeline_extractive_qa.py does NOT contain those tests.
    It must fail on the pre-merge version (where they exist) and pass on the merged version (where removed).
    """
    source = open("/workspace/test/test_pipeline_extractive_qa.py", "r", encoding="utf-8").read()

    forbidden_test_names = [
        "test_extractive_qa_es_authentication",
        "test_extractive_qa_document_store_authentication",
    ]

    for name in forbidden_test_names:
        assert re.search(rf"^\s*def\s+{re.escape(name)}\s*\(", source, flags=re.MULTILINE) is None, (
            f"Expected {name} to be removed from test/test_pipeline_extractive_qa.py after the review, "
            f"but it is still present. The review indicated these header/authentication tests were redundant/too expansive."
        )

    # Also ensure the specific authentication header used in those tests is not present anymore.
    assert "Authorization" not in source, (
        "Expected no explicit auth header tests in test/test_pipeline_extractive_qa.py after the review, "
        "but found 'Authorization' in the file."
    )