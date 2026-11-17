import re


def test_removed_es_authentication_tests_to_reduce_runtime_and_memory():
    """
    The review requested lowering memory footprint/runtime by removing the ES authentication
    tests that instantiated a reader and multiple retrievers (elasticsearch/dpr/embedding),
    and the follow-up commit removed those tests entirely.
    """
    path = "/workspace/test/test_pipeline_extractive_qa.py"
    source = open(path, "r", encoding="utf-8").read()

    assert "def test_extractive_qa_es_authentication" not in source, (
        "Expected the expensive ES authentication test to be removed to reduce runtime/memory "
        "(it used a reader and multiple retrievers), but it is still present in "
        f"{path}."
    )

    assert "def test_extractive_qa_document_store_authentication" not in source, (
        "Expected the document store authentication test to be removed as part of reducing "
        "runtime/memory footprint, but it is still present in "
        f"{path}."
    )

    # Ensure the expensive parametrization over multiple retrievers is gone.
    assert not re.search(
        r'@pytest\.mark\.parametrize\(\s*["\']retriever_with_docs["\']\s*,\s*\[\s*["\']elasticsearch["\']\s*,\s*["\']dpr["\']\s*,\s*["\']embedding["\']\s*\]',
        source,
        flags=re.MULTILINE,
    ), (
        "Expected parametrization over ['elasticsearch', 'dpr', 'embedding'] to be removed "
        "to reduce runtime/memory footprint, but it is still present."
    )