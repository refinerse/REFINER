import re


def test_auth_service_removes_redundant_through_api_key_flag_and_uses_tuple_return():
    """
    The review comment questions redundancy in the token parsing logic.
    The "after" code removes the redundant `through_api_key` boolean flag and
    instead directly branches to `get_user_and_scopes_with_api_key()` returning
    `(user, token_scopes)`.

    This test inspects the source to ensure:
      1) the redundant flag is gone
      2) the new helper API is used with tuple assignment
      3) the old helper `get_user_with_api_key` is removed
    """
    source = open("/workspace/xinference/api/oauth2/auth_service.py", "r", encoding="utf-8").read()

    assert "through_api_key" not in source, (
        "Expected redundant `through_api_key` flag to be removed; "
        "it indicates the older, more redundant control flow is still present."
    )

    assert re.search(
        r"user\s*,\s*token_scopes\s*=\s*self\.get_user_and_scopes_with_api_key\(\s*token\s*\)",
        source,
    ), (
        "Expected API-key authentication branch to assign both `user` and `token_scopes` "
        "from `get_user_and_scopes_with_api_key(token)`; not found."
    )

    assert "def get_user_and_scopes_with_api_key" in source, (
        "Expected new helper `get_user_and_scopes_with_api_key` to exist."
    )

    assert "def get_user_with_api_key" not in source, (
        "Expected old helper `get_user_with_api_key` to be removed in favor of "
        "`get_user_and_scopes_with_api_key`."
    )