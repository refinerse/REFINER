import re

import lib.ansible.modules.network.meraki.meraki_admin as meraki_admin


def _extract_documentation_block(source: str) -> str:
    m = re.search(r"(?ms)^DOCUMENTATION\s*=\s*r'''(.*?)'''", source)
    assert m, "Could not locate DOCUMENTATION r'''...''' block in meraki_admin.py"
    return m.group(1)


def test_documentation_defines_suboptions_for_tags_and_networks():
    """
    Style/doc change: tags and networks should document their dict structure via
    'suboptions' (tag/access for tags; id/access for networks).
    """
    source = open("/workspace/lib/ansible/modules/network/meraki/meraki_admin.py", "r", encoding="utf-8").read()
    doc = _extract_documentation_block(source)

    # Locate the 'tags:' option block and ensure it defines suboptions tag/access.
    tags_block = re.search(r"(?ms)^\s{4}tags:\n(.*?)(?=^\s{4}\w+:|\Z)", doc)
    assert tags_block, "DOCUMENTATION is missing the 'tags' option block"
    tags_text = tags_block.group(1)
    assert re.search(r"(?m)^\s{8}suboptions:\s*$", tags_text), (
        "DOCUMENTATION 'tags' option must define 'suboptions' describing the dict keys "
        "(expected after review); missing 'suboptions:' under 'tags:'"
    )
    assert re.search(r"(?m)^\s{12}tag:\s*$", tags_text), (
        "DOCUMENTATION 'tags' suboptions must include a 'tag' key description"
    )
    assert re.search(r"(?m)^\s{12}access:\s*$", tags_text), (
        "DOCUMENTATION 'tags' suboptions must include an 'access' key description"
    )

    # Locate the 'networks:' option block and ensure it defines suboptions id/access.
    networks_block = re.search(r"(?ms)^\s{4}networks:\n(.*?)(?=^\s{4}\w+:|\Z)", doc)
    assert networks_block, "DOCUMENTATION is missing the 'networks' option block"
    networks_text = networks_block.group(1)
    assert re.search(r"(?m)^\s{8}suboptions:\s*$", networks_text), (
        "DOCUMENTATION 'networks' option must define 'suboptions' describing the dict keys "
        "(expected after review); missing 'suboptions:' under 'networks:'"
    )
    assert re.search(r"(?m)^\s{12}id:\s*$", networks_text), (
        "DOCUMENTATION 'networks' suboptions must include an 'id' key description"
    )
    assert re.search(r"(?m)^\s{12}access:\s*$", networks_text), (
        "DOCUMENTATION 'networks' suboptions must include an 'access' key description"
    )