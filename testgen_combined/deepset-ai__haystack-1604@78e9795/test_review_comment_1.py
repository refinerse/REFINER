import re


def test_delete_labels_signature_accepts_ids_param_for_consistency():
    """
    The review comment requests consistent deletion signatures:
    delete_labels should accept `ids` (like delete_documents), not only `filters`.

    We assert the delete_labels method signature includes an `ids` parameter.
    """
    source = open("/workspace/haystack/document_store/elasticsearch.py", "r", encoding="utf-8").read()

    # Find the first definition of delete_labels in the file and capture its parameter list.
    m = re.search(r"\n\s*def\s+delete_labels\s*\(([^)]*)\)\s*:", source)
    assert m is not None, "Expected ElasticsearchDocumentStore.delete_labels() to be defined in elasticsearch.py"

    params = m.group(1)

    assert "ids" in params, (
        "delete_labels() should accept an `ids` parameter for API consistency with delete_documents(). "
        f"Found signature parameters: ({params})"
    )