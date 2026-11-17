import re


def test_headers_param_docstring_has_expected_example_capitalization_and_elasticsearch_wording():
    source = open("/workspace/haystack/document_stores/elasticsearch.py", "r", encoding="utf-8").read()

    # The review requested:
    # 1) Provide a real expected dict example like {'Authorization': 'Basic ...'} (not "meta description")
    # 2) Capitalize the sentence and replace "es" with "elasticsearch"
    # 3) Optional link to ES docs for supported headers
    #
    # We assert for the updated phrasing and example (must fail on "before").
    assert "Custom HTTP headers to pass to elasticsearch client" in source, (
        "Expected updated docstring wording with capitalization and 'elasticsearch client' "
        "(not 'custom HTTP headers to pass to es client')."
    )

    assert "{'Authorization': 'Basic " in source, (
        "Expected docstrings to include a concrete headers dict example like "
        "{'Authorization': 'Basic YWRtaW46cm9vdA=='}."
    )

    assert "https://www.elastic.co/guide/en/elasticsearch/reference/current/http-clients.html" in source, (
        "Expected docstrings to include a link to Elasticsearch documentation about HTTP clients/headers."
    )

    # Ensure the old phrasing is not present anymore (guards against partial update).
    assert "custom HTTP headers to pass to es client" not in source, (
        "Found old docstring phrasing 'custom HTTP headers to pass to es client'; "
        "it should be replaced with the capitalized 'Custom ... elasticsearch client' version."
    )

    # Additional guard: avoid "meta description" example phrasing from the before version.
    # (Before: "(e.g. user token with 'Authorization' header)")
    assert "user token with 'Authorization' header" not in source, (
        "Found old meta-description example \"user token with 'Authorization' header\"; "
        "expected a concrete dict example instead."
    )

    # At least one of the relevant functions should document headers using the new format.
    # We specifically check get_metadata_values_by_key's docstring block contains the new headers line.
    m = re.search(
        r"def get_metadata_values_by_key\([\s\S]*?\):\n\s+\"\"\"([\s\S]*?)\"\"\"",
        source,
    )
    assert m, "Could not locate get_metadata_values_by_key docstring to verify updated headers documentation."
    doc = m.group(1)
    assert "Custom HTTP headers to pass to elasticsearch client" in doc and "{'Authorization': 'Basic " in doc, (
        "Expected get_metadata_values_by_key docstring to include the updated 'headers' parameter description "
        "with a concrete Authorization dict example."
    )