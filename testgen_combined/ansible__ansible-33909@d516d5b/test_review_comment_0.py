import re

import lib.ansible.modules.network.iosxr.iosxr_interface as iosxr_interface


def test_enabled_option_documentation_uses_bool_type_not_choices():
    """
    Review requested doc change: for option 'enabled' in DOCUMENTATION YAML,
    replace choices ['True','False'] with 'type: bool'.

    This test parses the module's DOCUMENTATION string and asserts that:
      - enabled has 'type: bool'
      - enabled does NOT document boolean values via 'choices: [True, False]'
    """
    doc = iosxr_interface.DOCUMENTATION
    assert isinstance(doc, str) and doc.strip(), "Expected module to expose DOCUMENTATION as a non-empty string"

    # Extract the 'enabled:' option block (stop at next top-level option key)
    m = re.search(
        r"(?ms)^\s{2}enabled:\n(?P<body>.*?)(?=^\s{2}[a-zA-Z_][a-zA-Z0-9_]*:\n|\Z)",
        doc,
    )
    assert m, "Could not locate the 'enabled' option block inside DOCUMENTATION"

    enabled_block = "  enabled:\n" + m.group("body")

    assert re.search(r"(?m)^\s{4}type:\s*bool\s*$", enabled_block), (
        "DOCUMENTATION for option 'enabled' must specify 'type: bool' "
        "(as requested in the review comment)."
    )

    assert not re.search(r"(?m)^\s{4}choices:\s*\[.*\]\s*$", enabled_block), (
        "DOCUMENTATION for option 'enabled' should not use 'choices' to represent booleans; "
        "it should use 'type: bool' instead."
    )