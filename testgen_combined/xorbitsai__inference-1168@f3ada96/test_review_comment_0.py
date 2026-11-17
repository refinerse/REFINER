import re


def test_user_assignment_is_inside_if_else_branch_for_token_type():
    """
    Review intent: "Just let the `user` inside the `if else`."

    Enforce that `__call__` assigns `user` *within* the token-type branching
    (api key vs jwt), rather than using a separate `through_api_key` flag and
    assigning `user` afterward.
    """
    source = open("/workspace/xinference/api/oauth2/auth_service.py").read()

    # BEFORE code used a flag and assigned `user` later:
    #   through_api_key = False
    #   ...
    #   if not through_api_key:
    #       user = self.get_user(...)
    #   else:
    #       user = self.get_user_with_api_key(...)
    assert (
        "through_api_key" not in source
    ), "AuthService.__call__ should not use a 'through_api_key' flag; user selection should be inside the if/else branch."

    # AFTER code assigns `user` directly inside `if self.is_legal_api_key(token): ... else: ...`
    # via get_user_and_scopes_with_api_key / jwt decode path.
    assert re.search(
        r"if\s+self\.is_legal_api_key\(token\)\s*:\s*\n\s*user\s*,\s*token_scopes\s*=\s*self\.get_user_and_scopes_with_api_key\(token\)\s*\n\s*else\s*:",
        source,
        re.MULTILINE,
    ), (
        "Expected AuthService.__call__ to assign `user` (and `token_scopes`) inside the "
        "`if self.is_legal_api_key(token) ... else ...` branches."
    )