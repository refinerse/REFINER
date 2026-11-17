import re

import lib.ansible.modules.crypto.luks_device as luks_device


def test_documentation_requirements_mentions_wipefs_only_for_absent_state():
    """
    Style regression test for module DOCUMENTATION requirements line:

    Review requested:
        - "wipefs (when I(state) is C(absent))"

    Before: listed plain "wipefs" (unconditional) or incorrect wording.
    After: should explicitly document it is only needed for state=absent.
    """
    doc = luks_device.DOCUMENTATION

    # Extract the requirements block text from the DOCUMENTATION YAML-ish string
    m = re.search(r"\nrequirements:\n(?P<body>.*?)(?:\n\w[\w_]*:\n|\n'''|\Z)", doc, flags=re.S)
    assert m, "Could not locate a 'requirements:' section in luks_device.DOCUMENTATION"
    req_block = m.group("body")

    assert (
        '"wipefs (when I(state) is C(absent))"' in req_block
    ), (
        "Expected DOCUMENTATION requirements to contain the exact string "
        '"wipefs (when I(state) is C(absent))" to clarify wipefs is only needed '
        "when state=absent."
    )