import re


def test_e2e_mysql_compose_removes_posthog_keys_and_disables_posthog():
    """
    Regression test for review comment:
    - POSTHOG keys/hosts must not be committed in this compose file
    - POSTHOG_DISABLED=true must be set
    """
    path = "/workspace/tests/e2e_tests/docker-compose-e2e-mysql.yml"
    source = open(path, "r", encoding="utf-8").read()

    assert "POSTHOG_DISABLED=true" in source, (
        "docker-compose-e2e-mysql.yml must explicitly disable PostHog by setting "
        "POSTHOG_DISABLED=true in the environment."
    )

    forbidden_patterns = [
        r"\bPOSTHOG_KEY\s*=",
        r"\bPOSTHOG_HOST\s*=",
        r"\bNEXT_PUBLIC_POSTHOG_KEY\s*=",
        r"\bNEXT_PUBLIC_POSTHOG_HOST\s*=",
    ]
    for pat in forbidden_patterns:
        assert re.search(pat, source) is None, (
            f"Found PostHog credential/config entry matching /{pat}/ in {path}. "
            "POSTHOG_KEY/POSTHOG_HOST must be removed from the compose file."
        )