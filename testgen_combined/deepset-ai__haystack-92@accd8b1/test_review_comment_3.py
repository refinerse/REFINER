import re


def test_elasticsearch_retriever_eval_returns_map_metric_key():
    """
    The review comment requests naming the metric "map" (to match Finder.eval()).
    This test ensures ElasticsearchRetriever.eval() returns a dict containing "map"
    (and not the old "mean avg precision" key).
    """
    source = open("/workspace/haystack/retriever/elasticsearch.py", "r", encoding="utf-8").read()

    # Locate the return statement of ElasticsearchRetriever.eval specifically.
    # We check for an explicit dict literal containing "map": mean_avg_precision.
    has_map_return = re.search(
        r'return\s*\{\s*"recall"\s*:\s*recall\s*,\s*"map"\s*:\s*mean_avg_precision\s*\}',
        source,
        flags=re.MULTILINE,
    )
    assert has_map_return, (
        'ElasticsearchRetriever.eval() should return {"recall": recall, "map": mean_avg_precision} '
        'for consistency with Finder.eval(); expected "map" key to be present in the return dict.'
    )

    # Also ensure the old key is not used in the return dict anymore.
    old_key_in_return = re.search(
        r'return\s*\{[^}]*"mean avg precision"\s*:',
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert not old_key_in_return, (
        'ElasticsearchRetriever.eval() should not return the legacy "mean avg precision" key; '
        'it should be renamed to "map".'
    )