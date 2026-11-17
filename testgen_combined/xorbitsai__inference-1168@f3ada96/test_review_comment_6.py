import re


def test_api_key_pattern_uses_short_length_not_48():
    source = open("/workspace/xinference/api/oauth2/auth_service.py", "r", encoding="utf-8").read()

    # The review comment requests reducing the api-key token part length from 48 to 10 (total key length 16 with "sk-").
    # After fix, regex should enforce "^sk-[a-zA-Z0-9]{13}$" (13 chars after "sk-").
    assert (
        re.search(r"\^sk-\[a-zA-Z0-9\]\{13\}\$", source) is not None
        or re.search(r're\.compile\(["\']\^sk-\[a-zA-Z0-9\]\{13\}\$["\']\)', source)
        is not None
    ), (
        "AuthService.is_legal_api_key should validate API keys with a short format: "
        "'sk-' + 13 alnum chars (total length 16). Expected regex '^sk-[a-zA-Z0-9]{13}$'."
    )

    # Ensure we are not still using the old 48-char validation.
    assert "{48}" not in source, (
        "API key validation should not require 48 alnum characters; "
        "the old '{48}' pattern must be removed."
    )