import re


def test_init_envvars_uses_items_and_none_semantics():
    source = open("/workspace/qutebrowser/config/qtargs.py", encoding="utf-8").read()

    # Ensure the loop was changed to iterate over key/value pairs directly.
    assert (
        "for var, val in config.val.qt.environ.items():" in source
    ), (
        "Expected init_envvars to iterate over config.val.qt.environ.items() "
        "(for var, val in ...items()), as suggested in the review comment."
    )

    # Ensure the old pattern (iterate keys + index lookup + string 'None') is gone.
    assert (
        "for var in config.val.qt.environ:" not in source
    ), "Expected init_envvars to no longer iterate only over keys (for var in ...)."

    assert (
        "val = config.val.qt.environ[var]" not in source
    ), "Expected init_envvars to no longer index config.val.qt.environ[var] inside the loop."

    assert (
        "if val == 'None':" not in source
    ), "Expected init_envvars to no longer treat the string 'None' specially."

    # Ensure the new behavior is present: actual None deletes the env var.
    none_delete_pattern = re.compile(
        r"if\s+val\s+is\s+None\s+and\s+var\s+in\s+os\.environ\s*:\s*\n"
        r"\s*del\s+os\.environ\[var\]",
        re.MULTILINE,
    )
    assert none_delete_pattern.search(source), (
        "Expected init_envvars to delete os.environ[var] when the configured value is None "
        "and the variable exists (val is None -> del os.environ[var])."
    )