import re


def test_dns_utils_no_longer_defines_parse_systemd_resolve():
    """
    The merged ("after") version removed parse_systemd_resolve() from this module.
    The pre-merge ("before") version added it.

    Assert that /workspace/salt/utils/dns.py does NOT define parse_systemd_resolve.
    This fails on the "before" code and passes on the "after" code.
    """
    source = open("/workspace/salt/utils/dns.py", encoding="utf-8").read()

    # Anchor at beginning-of-line to avoid matching in comments/strings.
    assert re.search(r"^def\s+parse_systemd_resolve\s*\(", source, re.M) is None, (
        "Expected parse_systemd_resolve() to be absent from /workspace/salt/utils/dns.py "
        "in the corrected ('after') version."
    )