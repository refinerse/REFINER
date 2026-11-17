import re


def test_timeout_fixture_casts_envvar_to_int():
    """
    Source-level check: the timeout fixture should cast the env var (a string) to int.

    We intentionally avoid importing the module or relying on pytest plugins/conftest.
    """
    path = "/workspace/tests/pytests/scenarios/reauth/test_reauth.py"
    with open(path, encoding="utf-8") as f:
        source = f.read()

    # Find the return expression from the timeout fixture
    m = re.search(
        r"@pytest\.fixture\(scope=['\"]module['\"]\)\s*\n"
        r"def\s+timeout\s*\(\s*\)\s*:\s*\n"
        r"\s*return\s+(?P<expr>[^\n]+)",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, (
        f"Expected to find a module-scoped pytest fixture named 'timeout' in {path}"
    )

    expr = m.group("expr").strip()

    assert expr.startswith("int("), (
        "The 'timeout' fixture must cast the environment variable to int, e.g. "
        "`return int(os.environ.get('SALT_CI_REAUTH_MASTER_WAIT', 150))`, because "
        "os.environ.get(...) returns strings. "
        f"Found return expression: {expr!r}"
    )
    assert "SALT_CI_REAUTH_MASTER_WAIT" in expr, (
        "The 'timeout' fixture should read the 'SALT_CI_REAUTH_MASTER_WAIT' environment "
        f"variable. Found return expression: {expr!r}"
    )


# Ensure pytest does not auto-load external plugins which can cause internal errors
# in this execution environment (e.g., pytest-tempdir expecting config internals).
def pytest_addoption(parser):
    # no-op, but keeps this file as a valid pytest module without external plugin reliance
    return