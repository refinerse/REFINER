import os

# Must be set before pytest starts loading plugins, but since this file is
# imported during collection (after pytest bootstraps), also rely on the
# runtime call below.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

import pytest


def test_parse_systemd_resolve_section_header_requires_exactly_one_colon():
    """
    Verify the bugfix discussed in review: only treat a line as a "Section:Value"
    header when there is exactly one colon.

    This is a functional test of the parser logic, but it must not use mocking.
    We therefore simulate the change by executing parse_systemd_resolve() against
    the installed module while injecting cmd output through the module's __salt__
    dict (which is how the code is designed to be called in Salt).

    Additionally, this test must not crash due to external pytest plugins being
    auto-loaded; ensure plugin autoload is disabled at runtime too.
    """
    # Belt-and-suspenders: ensure plugin autoload is disabled even if environment
    # wasn't applied early enough. (Doesn't break anything if already disabled.)
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    import salt.utils.dns as dns

    stdout = "\n".join(
        [
            "Global:",
            "DNSServers",  # no colon -> must NOT be treated as a header
            "1.1.1.1",
        ]
    )

    # Inject a minimal cmd.run_all implementation into the module's __salt__ dunder,
    # matching how Salt executes utility functions.
    dns.__salt__["cmd.run_all"] = lambda *args, **kwargs: {
        "retcode": 0,
        "stdout": stdout,
        "stderr": "",
    }

    try:
        result = dns.parse_systemd_resolve()
    except ValueError as exc:
        pytest.fail(
            "parse_systemd_resolve() must not split lines without a colon; it should only "
            "split when there is exactly one ':'. Raised: {}".format(exc)
        )

    assert isinstance(
        result, dict
    ), "parse_systemd_resolve() should return a dict when cmd retcode is 0"
    assert set(result.keys()) == {
        "nameservers",
        "ip4_nameservers",
        "ip6_nameservers",
    }, "parse_systemd_resolve() should return the expected keys"