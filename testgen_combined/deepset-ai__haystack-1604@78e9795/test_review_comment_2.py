import re


def test_delete_labels_uses_user_facing_id_not_internal__id():
    """
    Style/API consistency: users should filter by 'id' rather than Elasticsearch internal '_id'.
    This test verifies that delete_labels documentation/examples do not expose '_id' and that
    the method signature supports ids explicitly.
    """
    source = open("/workspace/haystack/document_store/elasticsearch.py", "r", encoding="utf-8").read()

    # Narrow to the delete_labels method docstring region to avoid false positives elsewhere.
    m = re.search(r"def\s+delete_labels\s*\([^\)]*\):\s*\n\s*\"\"\"(.*?)\"\"\"", source, re.DOTALL)
    assert m is not None, "Expected ElasticsearchDocumentStore.delete_labels() to exist with a docstring."
    delete_labels_doc = m.group(1)

    assert '"_id"' not in delete_labels_doc, (
        "delete_labels() docstring should not expose Elasticsearch internal field '_id' in examples; "
        "it should use the user-facing 'id' field."
    )
    assert '"id"' in delete_labels_doc, (
        "delete_labels() docstring should include an example using the user-facing 'id' field "
        "(consistent with other document stores)."
    )

    # Ensure public API includes ids parameter (consistent with delete_documents and hiding ES internals).
    sig = re.search(r"def\s+delete_labels\s*\(([^)]*)\)", source)
    assert sig is not None, "Could not find delete_labels() signature."
    params = sig.group(1)
    assert re.search(r"\bids\s*:\s*Optional\[List\[str\]\]\s*=\s*None\b", params), (
        "delete_labels() should accept an explicit 'ids: Optional[List[str]] = None' parameter "
        "instead of requiring filters on Elasticsearch internal fields."
    )