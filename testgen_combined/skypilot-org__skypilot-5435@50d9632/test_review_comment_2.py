import re


def test_override_sky_config_uses_config_utils_set_nested_not_manual_dict_merge():
    source = open("/workspace/tests/smoke_tests/smoke_tests_utils.py", "r").read()

    # The review comment suggests switching override_sky_config_dict from a plain
    # dict + deep_update to a config_utils.Config and using set_nested.
    #
    # Before: had a nested python dict assignment like:
    #   override_sky_config_dict['jobs'] = {'controller': {'resources': {'cloud': ...}}}
    # After: should use:
    #   override_sky_config_dict = skypilot_config.config_utils.Config()
    #   override_sky_config_dict.set_nested(('jobs','controller','resources','cloud'), ...)
    assert "def override_sky_config(" in source, (
        "Expected override_sky_config() to exist in "
        "/workspace/tests/smoke_tests/smoke_tests_utils.py"
    )

    assert "override_sky_config_dict = skypilot_config.config_utils.Config()" in source, (
        "override_sky_config() should create override_sky_config_dict as a "
        "skypilot_config.config_utils.Config (as suggested in the review comment), "
        "not a plain dict."
    )

    # Ensure the key replacement behavior: set_nested is used for jobs/controller/resources/cloud.
    assert re.search(
        r"override_sky_config_dict\.set_nested\(\s*\(\s*'jobs'\s*,\s*'controller'\s*,\s*'resources'\s*,\s*'cloud'\s*\)",
        source,
    ), (
        "override_sky_config() should use Config.set_nested(('jobs','controller','resources','cloud'), ...) "
        "to set the controller cloud override."
    )

    # Ensure we did not keep the old dict-based approach for this specific key.
    assert "override_sky_config_dict['jobs']" not in source, (
        "override_sky_config() should not assign override_sky_config_dict['jobs'] directly; "
        "it should rely on Config.set_nested() for nested updates."
    )

    # Ensure the manual deep_update helper is removed (signals using Config overlay instead).
    assert "def deep_update" not in source, (
        "override_sky_config() should not define a manual deep_update() helper; "
        "Config.set_nested()/overlay_skypilot_config should be used instead."
    )