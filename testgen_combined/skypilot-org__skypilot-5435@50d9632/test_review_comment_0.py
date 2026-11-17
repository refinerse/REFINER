def test_override_sky_config_uses_skypilot_config_parser_and_overlay():
    source = open("/workspace/tests/smoke_tests/smoke_tests_utils.py", "r").read()

    # After the fix, override_sky_config should reuse SkyPilot's config parsing
    # and overlay utilities (instead of manual yaml.safe_load + custom deep merge).
    assert "skypilot_config.parse_config_file" in source, (
        "override_sky_config() should parse existing config via "
        "skypilot_config.parse_config_file(...) rather than using yaml.safe_load."
    )
    assert "skypilot_config.overlay_skypilot_config" in source, (
        "override_sky_config() should merge overrides via "
        "skypilot_config.overlay_skypilot_config(...) rather than a custom deep_update."
    )

    # Ensure legacy manual approach is removed.
    assert "def deep_update" not in source, (
        "override_sky_config() should not define a custom deep_update(); "
        "it should rely on SkyPilot config utilities."
    )
    assert "yaml.safe_load" not in source, (
        "override_sky_config() should not use yaml.safe_load directly; "
        "it should use skypilot_config.parse_config_file(...)."
    )