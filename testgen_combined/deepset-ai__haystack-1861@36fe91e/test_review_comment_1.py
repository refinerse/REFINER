import re


def test_get_document_by_id_does_not_accept_kwargs_anymore():
    """
    Regression test for a documentation/signature change discussed in review:
    `get_document_by_id` should not include a `**kwargs` parameter (it was only
    there to satisfy mypy/supertype compatibility previously).
    """
    source = open("/workspace/haystack/document_stores/elasticsearch.py", "r", encoding="utf-8").read()

    # Locate the first occurrence of the method definition (class has only one for ElasticsearchDocumentStore)
    m = re.search(r"\n\s*def\s+get_document_by_id\s*\(([^)]*)\)\s*->", source)
    assert m, "Could not find get_document_by_id() definition in /workspace/haystack/document_stores/elasticsearch.py"

    params = m.group(1)

    assert "**kwargs" not in params, (
        "get_document_by_id() should not accept arbitrary **kwargs anymore. "
        "The updated signature should explicitly list supported parameters (id, index, headers) "
        "without **kwargs."
    )