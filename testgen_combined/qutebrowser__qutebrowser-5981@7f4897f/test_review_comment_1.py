import re


def test_init_envvars_unsets_envvar_instead_of_setting_empty_string():
    """Ensure qtargs.init_envvars deletes env vars when config value is None.

    The reviewed change replaces setting os.environ[var] = '' (empty string)
    with actually deleting the key via `del os.environ[var]`, guarded by
    `if val is None and var in os.environ`.
    """
    source = open("/workspace/qutebrowser/config/qtargs.py", encoding="utf-8").read()

    # Old/broken behavior: when configured to be "None", envvar is set to ''.
    assert "os.environ[var] = ''" not in source, (
        "qtargs.init_envvars should *unset* an environment variable when the config "
        "value is None, not set it to an empty string. Found `os.environ[var] = ''` "
        "which indicates the old behavior."
    )

    # New/desired behavior: delete key from os.environ.
    assert re.search(r"\bdel\s+os\.environ\[\s*var\s*\]", source), (
        "qtargs.init_envvars should delete/unset the environment variable using "
        "`del os.environ[var]` when the config value is None."
    )

    # Ensure we don't delete unconditionally (should be guarded to avoid KeyError).
    assert "if val is None and var in os.environ" in source, (
        "Unsetting should be guarded with `if val is None and var in os.environ` "
        "to avoid KeyError when the variable isn't present."
    )