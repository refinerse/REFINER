import os

# IMPORTANT: disable third-party pytest plugin auto-loading (e.g., saltfactories),
# otherwise pytest may crash before running any tests due to duplicate options.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


def test_parse_systemd_resolve_removed():
    import salt.utils.dns as dns

    assert not hasattr(
        dns, "parse_systemd_resolve"
    ), (
        "parse_systemd_resolve() should not exist in salt.utils.dns; "
        "the systemd-resolve parsing code was removed."
    )