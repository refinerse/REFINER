import re


def test_auth_service_does_not_use_through_api_key_bool_flag():
    """
    The review comment asks to remove the unnecessary boolean variable
    `through_api_key` and directly branch on `self.is_legal_api_key(token)`.

    Since importing xinference.api.oauth2.auth_service fails in this environment,
    we verify via source inspection that the bool flag is not present.
    """
    path = "/workspace/xinference/api/oauth2/auth_service.py"
    source = open(path, "r", encoding="utf-8").read()

    assert (
        "through_api_key" not in source
    ), "AuthService.__call__ should not use a temporary boolean flag like `through_api_key`; it should branch directly on `self.is_legal_api_key(token)`."

    # Also ensure the direct branching pattern is present (sanity check).
    # This is intentionally a simple regex (not AST-based) to avoid fragility.
    assert re.search(
        r"\bif\s+self\.is_legal_api_key\(token\)\s*:",
        source,
    ), "AuthService.__call__ should directly branch on `if self.is_legal_api_key(token):`."