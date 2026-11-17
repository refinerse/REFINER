import re


def test_total_keys_renamed_to_all_api_keys():
    source_path = "/workspace/xinference/api/oauth2/auth_service.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # The review comment requests renaming the variable to `all_api_keys`.
    assert (
        re.search(r"^\s*all_api_keys\s*=\s*set\(\)\s*$", source, flags=re.MULTILINE)
        is not None
    ), (
        "Expected init_auth_config() to initialize a set named `all_api_keys` "
        "(e.g., `all_api_keys = set()`). This enforces the style rename requested "
        "in the code review."
    )

    assert (
        re.search(r"^\s*total_keys\s*=\s*set\(\)\s*$", source, flags=re.MULTILINE)
        is None
    ), (
        "Found `total_keys = set()` in auth_service.py. The review requested renaming "
        "`total_keys` to `all_api_keys`, so `total_keys` should no longer be present."
    )