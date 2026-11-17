import re


def test_asn_section_header_comment_is_asns_not_rirs():
    """
    Style check: The section header comment immediately preceding ASNTable
    should read '# ASNs' (not '# RIRs').
    """
    source = open("/workspace/netbox/ipam/tables/ip.py", encoding="utf-8").read()

    # Find the header comment block immediately before the ASNTable definition
    m = re.search(
        r"(?ms)\n#\n#\s*(?P<header>[^#\n]+?)\s*\n#\n\s*\nclass\s+ASNTable\b",
        source,
    )
    assert m is not None, (
        "Could not locate a section header comment block immediately preceding "
        "the 'class ASNTable' definition in /workspace/netbox/ipam/tables/ip.py."
    )

    header = m.group("header").strip()
    assert header == "ASNs", (
        "Expected ASNTable to be under a section header comment '# ASNs' to match style. "
        f"Found header '# {header}' immediately preceding ASNTable."
    )