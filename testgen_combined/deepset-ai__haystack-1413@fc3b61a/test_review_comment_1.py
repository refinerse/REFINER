import re


def test_most_similar_documents_pipeline_uses_explicit_document_ids_instead_of_collecting_from_store():
    source = open("/workspace/test/test_pipeline.py", "r", encoding="utf-8").read()

    # The review change removes the unnecessary for-loop that collects the first two IDs
    # from `document_store.get_all_documents(...)` and instead uses explicit IDs in the
    # documents list (and sets `docs_id = ["a", "b"]`).
    assert "MostSimilarDocumentsPipeline" in source, "Sanity check: expected MostSimilarDocumentsPipeline usage in test/test_pipeline.py"

    assert 'docs_id: list = ["a", "b"]' in source, (
        "Expected the test to use explicit document IDs (docs_id = ['a', 'b']) instead of collecting IDs via a for-loop."
    )

    assert '"id": "a"' in source and '"id": "b"' in source, (
        "Expected documents to define explicit IDs ('a' and 'b') inline in the documents payload."
    )

    # Ensure the old loop-based ID collection pattern is not present anymore.
    loop_pattern = re.compile(
        r"docs_id\s*:\s*list\s*=\s*\[\]\s*\n\s*for\s+index\s*,\s*doc\s+in\s+enumerate\(\s*document_store\.get_all_documents",
        re.MULTILINE,
    )
    assert not loop_pattern.search(source), (
        "Did not expect to find the old for-loop collecting doc IDs from document_store.get_all_documents(); "
        "the review requested removing this loop in favor of explicit IDs."
    )