import re


def test_ovirt_host_id_option_describes_host_not_nic():
    """
    Functional intent of review: the 'id' option in DOCUMENTATION should refer to a host,
    not a NIC. Since importing ansible modules fails in this environment, verify by
    inspecting the module source text.
    """
    source = open("/workspace/lib/ansible/modules/cloud/ovirt/ovirt_host.py", "r", encoding="utf-8").read()

    # Locate the "options: id: description" block and ensure it mentions "host", not "nic".
    # Keep the match bounded to avoid false positives from other occurrences of "host".
    m = re.search(
        r"(?ms)^options:\s*\n"
        r"(?:^[ \t]+\w+:\s*\n.*?\n)*?"  # any options before id
        r"^[ \t]+id:\s*\n"
        r"^[ \t]+description:\s*\n"
        r"(?P<desc>(?:^[ \t]+-\s+\".*?\"\s*\n)+)",
        source,
    )
    assert m, "Could not find DOCUMENTATION options.id.description block in ovirt_host module source."

    desc_block = m.group("desc")
    assert "ID of the host to manage." in desc_block, (
        "The 'id' option description should say it manages a host (not a nic). "
        f"Found description block:\n{desc_block}"
    )
    assert "ID of the nic to manage." not in desc_block, (
        "The 'id' option description must not refer to a nic; it should refer to a host. "
        f"Found description block:\n{desc_block}"
    )