import re


def test_eval_docstring_is_documentstore_generic_and_return_key_is_map():
    source = open("/workspace/haystack/retriever/elasticsearch.py", "r", encoding="utf-8").read()

    # Docstring should be generic (not Elasticsearch-specific) for label_index/doc_index params.
    assert (
        "Index/Table in DocumentStore where labeled questions are stored" in source
    ), (
        "Expected eval() docstring to describe label_index generically as "
        "'Index/Table in DocumentStore where labeled questions are stored' (not Elasticsearch-specific)."
    )
    assert (
        "Elasticsearch index where labeled questions are stored" not in source
    ), (
        "eval() docstring still contains Elasticsearch-specific wording for label_index; "
        "it should be generic to support other DocumentStores."
    )

    # Return dict key should be 'map' (the corrected API), but the phrase "mean avg precision"
    # is still expected to appear in the docstring text describing the metric name in prose.
    assert re.search(
        r'return\s*\{\s*"recall"\s*:\s*recall\s*,\s*"map"\s*:\s*mean_avg_precision\s*\}',
        source,
    ), (
        "Expected eval() to return {'recall': recall, 'map': mean_avg_precision}. "
        "This enforces the updated metric naming."
    )

    # Ensure we are not still returning the old key name.
    assert not re.search(
        r'return\s*\{[^}]*"mean avg precision"\s*:',
        source,
        flags=re.DOTALL,
    ), (
        "eval() still appears to return a key named 'mean avg precision'. "
        "It should return 'map' instead."
    )