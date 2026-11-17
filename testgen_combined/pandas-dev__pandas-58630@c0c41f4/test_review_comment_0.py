import re


def test_groupby_tuple_keys_handle_multiindex_uses_include_groups_false():
    source = open(
        "/workspace/pandas/tests/groupby/test_grouping.py", encoding="utf-8"
    ).read()

    # Extract only the body of the target test to avoid matching unrelated occurrences.
    m = re.search(
        r"def test_groupby_tuple_keys_handle_multiindex\(self\):(?P<body>.*?)(?:\n\s*def |\Z)",
        source,
        flags=re.S,
    )
    assert m is not None, (
        "Expected to find 'test_groupby_tuple_keys_handle_multiindex' in "
        "/workspace/pandas/tests/groupby/test_grouping.py"
    )
    body = m.group("body")

    assert "include_groups=False" in body, (
        "This test should pass include_groups=False to GroupBy.apply to avoid the "
        "DeprecationWarning about operating on grouping columns. "
        "Expected 'include_groups=False' within the body of "
        "test_groupby_tuple_keys_handle_multiindex."
    )