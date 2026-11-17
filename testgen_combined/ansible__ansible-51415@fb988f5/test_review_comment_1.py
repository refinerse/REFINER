import re

import lib.ansible.modules.network.meraki.meraki_admin as meraki_admin


def _documentation_block():
    # Module stores DOCUMENTATION as a raw YAML-ish string used by Ansible docs tooling.
    doc = getattr(meraki_admin, "DOCUMENTATION", None)
    assert isinstance(doc, str) and doc.strip(), "Expected module to expose DOCUMENTATION as a non-empty string"
    return doc


def _option_block(doc: str, option_name: str) -> str:
    """
    Extract the YAML-ish block for a top-level option (e.g. 'networks:'), up to the next
    top-level option (same indent) or end of DOCUMENTATION.
    """
    # options are indented by 4 spaces in this module's DOCUMENTATION
    m = re.search(rf"(?ms)^\s{{4}}{re.escape(option_name)}:\s*\n(.*?)(?=^\s{{4}}\w+:\s*\n|\Z)", doc)
    assert m, f"Could not locate '{option_name}:' option block in DOCUMENTATION"
    return m.group(0)


def test_networks_option_uses_suboptions_for_id_and_access_and_mentions_valid_access_choices():
    """
    Review requested switching from ad-hoc description lines to structured 'suboptions'
    (as used in other modules), and documenting access allowed values.

    This test enforces that the 'networks' option:
      - defines suboptions for 'id' and 'access'
      - documents that access valid options are full/read-only/none
    """
    doc = _documentation_block()
    networks_block = _option_block(doc, "networks")

    assert "suboptions:" in networks_block, (
        "The 'networks' option should use Ansible DOCUMENTATION 'suboptions' to describe "
        "the dict fields (id/access), rather than only freeform description lines."
    )
    assert re.search(r"(?m)^\s{12}id:\s*$", networks_block), (
        "The 'networks' option should define a suboption named 'id:' under suboptions."
    )
    assert re.search(r"(?m)^\s{12}access:\s*$", networks_block), (
        "The 'networks' option should define a suboption named 'access:' under suboptions."
    )
    assert re.search(r"Valid options are\s+C\(full\).+C\(read-only\).+C\(none\)", networks_block, re.DOTALL), (
        "The 'networks.access' suboption description should state valid options are "
        "C(full), C(read-only), or C(none)."
    )