import re

import pytest


def test_delete_expired_items_uses_iter_stores_loop_style():
    source_path = "/workspace/localstack/services/dynamodb/provider.py"
    source = open(source_path).read()

    # The review comment requests iterating using the store helper:
    #   for account_id, region_name, state in dynamodb_stores.iter_stores():
    expected_line = "for account_id, region_name, state in dynamodb_stores.iter_stores():"
    assert (
        expected_line in source
    ), f"Expected DynamoDB store iteration to use iter_stores() style loop:\n  {expected_line}\nFile: {source_path}"

    # Ensure we no longer use the nested dict iteration style that existed before.
    # This is intentionally strict to make the test fail on the 'before' version.
    forbidden_pattern = (
        r"for account_id, account_bundle in dynamodb_stores\.items\(\):\s*\n"
        r"\s*for region_name, state in account_bundle\.items\(\):"
    )
    assert not re.search(
        forbidden_pattern, source, flags=re.MULTILINE
    ), (
        "Found old nested iteration over dynamodb_stores.items() and account_bundle.items(); "
        "expected a single iter_stores() loop instead. "
        f"File: {source_path}"
    )