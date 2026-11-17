import inspect

import haystack.database.elasticsearch as es


def test_elasticsearch_document_store_renamed_get_all_documents_in_index_method_exists_and_old_name_removed():
    """
    Style/API test: the helper for scanning docs in a specific index was renamed from
    `get_all_docs_in_index` to the clearer `get_all_documents_in_index`.

    This test enforces the public API surface:
    - new name must exist
    - old name must not exist
    """
    cls = es.ElasticsearchDocumentStore

    assert hasattr(
        cls, "get_all_documents_in_index"
    ), "Expected ElasticsearchDocumentStore to define `get_all_documents_in_index()` (renamed from `get_all_docs_in_index()`)."

    assert not hasattr(
        cls, "get_all_docs_in_index"
    ), "Did not expect ElasticsearchDocumentStore to expose `get_all_docs_in_index()` after rename; only `get_all_documents_in_index()` should exist."

    # Ensure the new attribute is actually a function defined on the class (not e.g. a property)
    member = getattr(cls, "get_all_documents_in_index")
    assert inspect.isfunction(
        member
    ), "`get_all_documents_in_index` should be a regular method defined on ElasticsearchDocumentStore."