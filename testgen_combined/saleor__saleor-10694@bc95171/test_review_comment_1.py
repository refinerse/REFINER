import re


def test_customers_filter_by_ids_checks_correct_user_returned():
    source = open("/workspace/saleor/graphql/account/tests/test_account.py").read()

    # The change requested in review: do not only assert that exactly one customer is returned,
    # but also verify it's the correct user by decoding the returned global ID and comparing it
    # to the searched user's pk.
    #
    # Before: `test_query_customers_with_filter_by_ids` only asserted `len(users) == 1`.
    # After:  it was replaced with `test_query_customers_with_filter_by_one_id` and includes
    #         `graphene.Node.from_global_id(...)` + `assert id == str(search_user.pk)`.

    assert (
        "def test_query_customers_with_filter_by_ids" not in source
    ), (
        "Expected the old test `test_query_customers_with_filter_by_ids` to be removed/replaced "
        "because it didn't verify that the returned user is the one requested by id."
    )

    assert (
        "def test_query_customers_with_filter_by_one_id" in source
    ), "Expected the new test `test_query_customers_with_filter_by_one_id` to be present."

    pattern_decode_and_compare = re.compile(
        r'def test_query_customers_with_filter_by_one_id[\s\S]*?'
        r'result_user\s*=\s*content\["data"\]\["customers"\]\["edges"\]\[0\][\s\S]*?'
        r'graphene\.Node\.from_global_id\(\s*result_user\["node"\]\["id"\]\s*\)[\s\S]*?'
        r"assert\s+id\s*==\s*str\(search_user\.pk\)",
        re.MULTILINE,
    )
    assert pattern_decode_and_compare.search(source), (
        "Expected `test_query_customers_with_filter_by_one_id` to decode the returned GraphQL "
        "node id (`result_user['node']['id']`) using `graphene.Node.from_global_id` and assert "
        "the decoded id equals `search_user.pk` (stringified). This ensures the response contains "
        "the correct user, not just any single user."
    )