import os

# Must be set before pytest starts importing external plugins.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


def test_parse_resolv_returns_empty_dict_on_oserror():
    import salt.utils.dns

    # Use a path which should reliably not exist.
    result = salt.utils.dns.parse_resolv("/this/path/does/not/exist/resolv.conf")
    assert result == {}, "parse_resolv() should return {} when fopen raises OSError."


def test_dns_module_does_not_define_parse_systemd_resolve():
    """
    The correct ('after') version removed parse_systemd_resolve(). Ensure it is
    not part of the public API and not present in the source.

    This fails on the 'before' version where parse_systemd_resolve() exists.
    """
    import salt.utils.dns

    assert not hasattr(
        salt.utils.dns, "parse_systemd_resolve"
    ), "parse_systemd_resolve() should not exist in salt.utils.dns."

    source = open("/workspace/salt/utils/dns.py", encoding="utf-8").read()
    assert (
        "def parse_systemd_resolve" not in source
    ), "salt/utils/dns.py should not define parse_systemd_resolve()."