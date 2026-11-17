import re


def test_override_sky_config_uses_overlay_skypilot_config_instead_of_deep_update():
    source = open("/workspace/tests/smoke_tests/smoke_tests_utils.py", "r").read()

    # The style change requested in the review is to reuse the existing config
    # overlay helper (overlay_skypilot_config) rather than defining a local
    # deep_update() merge helper.
    assert "def deep_update(" not in source, (
        "override_sky_config() should not define a local deep_update(); "
        "it should reuse skypilot_config.overlay_skypilot_config()."
    )

    assert "overlay_skypilot_config(" in source, (
        "override_sky_config() should call skypilot_config.overlay_skypilot_config() "
        "to overlay override config onto the original config."
    )

    # Extra guard: ensure the call is specifically through skypilot_config.*
    assert re.search(r"skypilot_config\.overlay_skypilot_config\s*\(", source), (
        "Expected override_sky_config() to invoke skypilot_config.overlay_skypilot_config(...)."
    )