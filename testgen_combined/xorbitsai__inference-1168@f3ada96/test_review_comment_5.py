import re


def test_duplicate_api_keys_error_message_and_pattern_updated():
    source = open("/workspace/xinference/api/oauth2/auth_service.py", "r").read()

    # Functional intent of the review: duplicates across users should raise the specific message.
    assert (
        "Duplicate api-keys exists, please check your configuration" in source
    ), (
        "AuthService.init_auth_config() should raise ValueError with message "
        "'Duplicate api-keys exists, please check your configuration' when api keys "
        "are duplicated across users."
    )

    # Ensure the API key legality check matches the updated format (sk- + 13 alnum).
    # This distinguishes before/after and ensures tests align with the new config validation.
    assert re.search(r're\.compile\("\^sk-\[a-zA-Z0-9\]\{13\}\$"\)', source), (
        "AuthService.is_legal_api_key() should enforce the updated API key format "
        "using pattern '^sk-[a-zA-Z0-9]{13}$'."
    )