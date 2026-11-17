import re


def test_mypy_plugin_collect_config_handles_populate_by_name_and_validate_flags():
    """
    Regression test for pydantic mypy plugin config handling.

    The plugin must treat `populate_by_name=True` as equivalent to `validate_by_name=True`
    for the purposes of:
      * suppressing "Required dynamic aliases disallowed" warnings, and
      * deciding whether to use aliases in the generated __init__ signature.

    Since `mypy` isn't available in this execution environment, we verify this via
    source inspection of /workspace/pydantic/mypy.py.
    """
    source = open("/workspace/pydantic/mypy.py", "r", encoding="utf-8").read()

    assert (
        "'populate_by_name'" in source
    ), "Expected the plugin to track 'populate_by_name' in tracked_config_fields for backwards compatibility."

    # The key logic change in collect_config(): dynamic alias warnings should be suppressed if
    # either validate_by_name or populate_by_name is enabled.
    assert (
        "not (config.validate_by_name or config.populate_by_name)" in source
    ), (
        "Expected collect_config() to suppress required-dynamic-alias warnings when either "
        "validate_by_name or populate_by_name is True."
    )

    # The key logic change in add_initializer(): alias usage should be disabled if validate_by_name OR
    # populate_by_name is enabled (and validate_by_alias is not explicitly False).
    assert (
        "use_alias = not (config.validate_by_name or config.populate_by_name) and config.validate_by_alias is not False"
        in source
    ), (
        "Expected add_initializer() to compute use_alias based on BOTH validate_by_name and populate_by_name, "
        "and respect validate_by_alias is not False."
    )

    # Ensure ModelConfigData supports populate_by_name; this is required for the above logic to work.
    assert re.search(r"def __init__\([\s\S]*\bpopulate_by_name:\s*bool\s*\|\s*None\s*=\s*None", source), (
        "Expected ModelConfigData.__init__ to accept a populate_by_name: bool | None = None parameter."
    )
    assert "self.populate_by_name = populate_by_name" in source, (
        "Expected ModelConfigData to store populate_by_name on self.populate_by_name."
    )