import re

import pytest


def test_query_by_embedding_signature_has_no_kwargs_and_headers_optional_dict():
    """
    The review comment asks why we need **kwargs (mypy signature incompatibility).
    The fix removes **kwargs from query_by_embedding signatures and also changes
    headers typing from MutableMapping[...] to Optional[Dict[str, str]].

    This test inspects the source to ensure:
      - ElasticsearchDocumentStore.query_by_embedding has no **kwargs
      - OpenSearchDocumentStore.query_by_embedding has no **kwargs
      - both use headers: Optional[Dict[str, str]] = None
    """
    source = open("/workspace/haystack/document_stores/elasticsearch.py", "r", encoding="utf-8").read()

    # Grab the parameter lists from both method definitions.
    es_match = re.search(
        r"class\s+ElasticsearchDocumentStore\b.*?\n\s+def\s+query_by_embedding\s*\((?P<params>.*?)\)\s*->",
        source,
        flags=re.DOTALL,
    )
    os_match = re.search(
        r"class\s+OpenSearchDocumentStore\b.*?\n\s+def\s+query_by_embedding\s*\((?P<params>.*?)\)\s*->",
        source,
        flags=re.DOTALL,
    )

    assert es_match, "Expected to find ElasticsearchDocumentStore.query_by_embedding definition in source."
    assert os_match, "Expected to find OpenSearchDocumentStore.query_by_embedding definition in source."

    es_params = es_match.group("params")
    os_params = os_match.group("params")

    assert "**kwargs" not in es_params, (
        "ElasticsearchDocumentStore.query_by_embedding should not accept **kwargs; "
        "it was added to silence mypy but makes the signature deviate from BaseDocumentStore."
    )
    assert "**kwargs" not in os_params, (
        "OpenSearchDocumentStore.query_by_embedding should not accept **kwargs; "
        "it was added to silence mypy but makes the signature deviate from BaseDocumentStore."
    )

    expected_headers_snippet = "headers: Optional[Dict[str, str]] = None"
    assert expected_headers_snippet in es_params, (
        "ElasticsearchDocumentStore.query_by_embedding should type headers as Optional[Dict[str, str]] = None "
        "(not MutableMapping[...] and not untyped)."
    )
    assert expected_headers_snippet in os_params, (
        "OpenSearchDocumentStore.query_by_embedding should type headers as Optional[Dict[str, str]] = None "
        "(not MutableMapping[...] and not untyped)."
    )