import re


def test_delete_expired_items_moves_client_connection_to_outer_loop():
    source = open("/workspace/localstack/services/dynamodb/provider.py").read()

    # Extract the body of delete_expired_items() to limit false positives elsewhere in the file
    m = re.search(r"(?ms)^def delete_expired_items\(\) -> int:\n(.*?)(?=^\n^def |\Z)", source)
    assert m, "Expected to find function definition `def delete_expired_items() -> int:` in provider.py"
    body = m.group(1)

    # Style expectation from review:
    # - connect_to(...).dynamodb should happen once per (account_id, region) store iteration,
    #   before the loop over ttl_specs.items()
    assert (
        "for account_id, region_name, state in dynamodb_stores.iter_stores()" in body
    ), "Expected delete_expired_items to iterate stores via `dynamodb_stores.iter_stores()` (account_id, region_name, state)"

    client_line = "client = connect_to(aws_access_key_id=account_id, region_name=region_name).dynamodb"
    assert (
        client_line in body
    ), "Expected delete_expired_items to create the DynamoDB client once per store: `client = connect_to(aws_access_key_id=account_id, region_name=region_name).dynamodb`"

    idx_client = body.index(client_line)
    idx_ttl_loop = body.index("for table_name, ttl_spec in ttl_specs.items():")

    assert (
        idx_client < idx_ttl_loop
    ), "Expected DynamoDB client creation to be moved outside the inner TTL/table loop (client should be created before iterating `ttl_specs.items()`)"

    # Ensure old (inefficient) pattern is not used anymore inside the TTL loop
    assert (
        "client = connect_to(region_name=region_name).dynamodb" not in body
    ), "Expected old pattern `client = connect_to(region_name=region_name).dynamodb` to be removed from delete_expired_items()"