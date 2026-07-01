import re

import lib.ansible.modules.network.onyx.onyx_bgp as onyx_bgp


def _get_purge_option_block(documentation: str) -> str:
    """
    Extract the YAML-ish option block for 'purge:' from the module DOCUMENTATION.
    We anchor on exactly two-space indentation since Ansible module docs are structured that way:
      options:
        <option_name>:
          ...
    """
    # Capture from "  purge:" up to (but not including) the next "  <option>:" at same indent.
    m = re.search(r"(?ms)^\s{2}purge:\s*\n(.*?)(?=^\s{2}\S+:\s*$|\Z)", documentation)
    assert m is not None, (
        "Could not find the 'purge:' option block under DOCUMENTATION 'options:'. "
        "Expected a block starting with two-space-indented 'purge:'."
    )
    return "  purge:\n" + m.group(1)


def test_purge_option_has_version_added_28_in_documentation():
    """
    Review requires: 'purge' option in DOCUMENTATION includes 'version_added: 2.8'.
    This should fail on the old code (missing version_added) and pass on the corrected code.
    """
    purge_block = _get_purge_option_block(onyx_bgp.DOCUMENTATION)

    assert re.search(r"(?m)^\s{4}version_added:\s*2\.8\s*$", purge_block), (
        "The 'purge' option must declare 'version_added: 2.8'. "
        f"Current purge block:\n{purge_block}"
    )