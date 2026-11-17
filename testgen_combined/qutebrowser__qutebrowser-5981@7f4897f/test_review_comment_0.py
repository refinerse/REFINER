import re


def test_init_envvars_uses_none_constant_and_deletes_envvar():
    source = open("/workspace/qutebrowser/config/qtargs.py", encoding="utf-8").read()

    # The old/broken behavior compared against the string 'None' and set the env var to ''.
    assert "if val == 'None':" not in source, (
        "init_envvars() must not compare config values against the string 'None'. "
        "It should check against the Python None constant instead."
    )
    assert "os.environ[var] = ''" not in source, (
        "init_envvars() must not set environment variables to an empty string when the "
        "config value is None; it should delete the env var (if present) instead."
    )

    # The new/correct behavior should check `val is None` and delete the env var.
    assert "if val is None" in source, (
        "init_envvars() should check `val is None` to detect YAML/JSON null values."
    )
    assert "del os.environ[var]" in source, (
        "When the config value is None and the env var exists, init_envvars() should "
        "delete it via `del os.environ[var]`."
    )

    # Also ensure it iterates items (var, val) to avoid repeated dict lookups.
    assert re.search(r"for\s+var\s*,\s*val\s+in\s+config\.val\.qt\.environ\.items\(\)\s*:", source), (
        "init_envvars() should iterate via "
        "`for var, val in config.val.qt.environ.items():`."
    )