import re


def test_most_similar_documents_pipeline_returns_documents_not_ids():
    source = open("/workspace/haystack/pipeline.py", "r", encoding="utf-8").read()

    # Focus on the behavior/documentation change requested in the review:
    # "Let's rather return a list of Documents here than just the ids"
    #
    # Before: returns a nested list of ids via found_document.id and return_ids.
    # After: returns list of Documents returned by query_by_embedding directly.
    assert "class MostSimilarDocumentsPipeline" in source, (
        "Expected MostSimilarDocumentsPipeline to exist in /workspace/haystack/pipeline.py"
    )

    assert "found_document.id" not in source, (
        "MostSimilarDocumentsPipeline should return Documents, not ids: "
        "found_document.id usage indicates it's collecting ids."
    )

    assert "return return_ids" not in source, (
        "MostSimilarDocumentsPipeline should not return a variable named return_ids; "
        "it should return the Documents returned by query_by_embedding."
    )

    # Positive check: pipeline should append the Document objects returned by query_by_embedding
    # rather than extracting their ids.
    assert re.search(r"similar_documents\.append\(\s*self\.document_store\.query_by_embedding\(", source), (
        "Expected MostSimilarDocumentsPipeline.run() to append the Documents returned by "
        "document_store.query_by_embedding(...) to similar_documents."
    )

    # Also verify the docstring aligns with returning similar documents, not ids.
    assert "most similar documents" in source.lower(), (
        "Expected MostSimilarDocumentsPipeline docstring to describe returning most similar documents (not ids)."
    )