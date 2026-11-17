import re


def test_docker_compose_db_auth_frontend_does_not_include_posthog_key_or_host():
    """
    The review comment ("This Posthog key too") indicates we should not commit a real PostHog key/host
    into the e2e docker-compose file. The fix removes POSTHOG_KEY and POSTHOG_HOST from the
    keep-frontend-db-auth service environment.
    """
    source = open("/workspace/tests/e2e_tests/docker-compose-e2e-postgres.yml", "r", encoding="utf-8").read()

    # Extract the keep-frontend-db-auth service block (everything until the next top-level service).
    m = re.search(
        r"(?ms)^\s{2}keep-frontend-db-auth:\n(.*?)(?=^\s{2}[a-zA-Z0-9_.-]+:\n|\Z)",
        source,
    )
    assert m is not None, "Expected to find the 'keep-frontend-db-auth' service definition in the compose file."

    block = m.group(0)

    assert "POSTHOG_KEY" not in block, (
        "keep-frontend-db-auth should not define POSTHOG_KEY in docker-compose-e2e-postgres.yml "
        "(avoid committing a PostHog key; use POSTHOG_DISABLED=true instead)."
    )
    assert "POSTHOG_HOST" not in block, (
        "keep-frontend-db-auth should not define POSTHOG_HOST in docker-compose-e2e-postgres.yml "
        "(avoid committing a PostHog host; use POSTHOG_DISABLED=true instead)."
    )