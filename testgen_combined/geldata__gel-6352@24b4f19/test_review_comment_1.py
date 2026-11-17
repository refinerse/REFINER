import re


def test_simple_http_default_auth_is_password_not_scram():
    source = open("/workspace/edb/server/args.py", "rt", encoding="utf-8").read()

    # The review comment indicates SIMPLE_HTTP should not be treated as SCRAM,
    # and a distinct Password auth method should exist and be used by default.
    assert re.search(r"\bPassword\s*=\s*['\"]Password['\"]", source), (
        "Expected ServerAuthMethod to define a distinct Password enum value "
        "(Password = 'Password') to avoid implying SIMPLE_HTTP uses SCRAM."
    )

    assert re.search(
        r"ServerConnTransport\.SIMPLE_HTTP\s*:\s*ServerAuthMethod\.Password",
        source,
    ), (
        "Expected DEFAULT_AUTH_METHODS to map SIMPLE_HTTP to Password "
        "(ServerAuthMethod.Password), not Scram."
    )