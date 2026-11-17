import re


def test_check_http_auth_extracts_username_from_http_auth_headers():
    source = open("/workspace/edb/server/protocol/protocol.pyx", "r", encoding="utf-8").read()

    # The key functional change requested in the review is: do not hardcode
    # user='edgedb'; instead extract the username from JWT/Basic/X-EdgeDB-User.
    #
    # Before: user = 'edgedb'  # I guess?
    # After:  username, opt_password = auth_helpers.extract_http_user(...)
    assert "user = 'edgedb'" not in source, (
        "HttpProtocol._check_http_auth must not hardcode user='edgedb'; "
        "it should extract the username from JWT 'bearer' or Basic auth / "
        "X-EdgeDB-User so cfg::Auth.user works for non-default roles."
    )

    assert re.search(r"extract_http_user\s*\(", source), (
        "HttpProtocol._check_http_auth should call auth_helpers.extract_http_user(...) "
        "to determine the role/username from the request auth data."
    )

    # Also verify it uses the extracted username in get_auth_method(), not a constant.
    assert "get_auth_method(\n                username" in source or "get_auth_method(\n                username," in source, (
        "HttpProtocol._check_http_auth should fetch auth method for the extracted "
        "username (role), not for a hardcoded 'edgedb' user."
    )