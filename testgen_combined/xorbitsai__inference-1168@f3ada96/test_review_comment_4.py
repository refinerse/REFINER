import re


def test_auth_service_deduplicates_api_key_logic_by_removing_per_user_duplicate_check():
    """
    Review comment asks whether logic is duplicated: previously code checked duplicates
    both within a user and across users. After change, duplicate detection is unified
    across all users (single set), and the per-user duplicate check is removed.
    """
    source = open("/workspace/xinference/api/oauth2/auth_service.py", "r", encoding="utf-8").read()

    # BEFORE had a per-user duplicate check:
    #   if len(set(user.api_keys)) != len(user.api_keys):
    #       raise ValueError("User has duplicate Api-Keys")
    #
    # AFTER removes that block and instead checks duplicates using a single global set.
    assert (
        "len(set(user.api_keys)) != len(user.api_keys)" not in source
    ), "Per-user duplicate API key check should be removed to avoid duplicated logic; duplicates should be detected via a single global set."

    # Also assert the global dedup logic exists as the replacement behavior.
    assert (
        re.search(r"\ball_api_keys\s*=\s*set\(\)", source) is not None
        or re.search(r"\btotal_keys\s*=\s*set\(\)", source) is not None
    ), "AuthService.init_auth_config should maintain a single set of all API keys to detect duplicates across the whole config."