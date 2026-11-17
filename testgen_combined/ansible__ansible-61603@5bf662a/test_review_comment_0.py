import re

import lib.ansible.modules.crypto.luks_device as luks_device


def test_documentation_label_description_uses_respectively_phrase():
    """
    Style check: ensure the label option documentation contains the reviewed wording
    'with label support, respectively to identify the container by'.

    This should fail on the pre-review text ('then late it could be used...') and
    pass once the reviewed wording is present.
    """
    doc = luks_device.DOCUMENTATION

    # Make whitespace robust across wrapping/indentation in YAML docstring.
    normalized = re.sub(r"\s+", " ", doc).strip()

    expected = "with label support, respectively to identify the container by"
    assert expected in normalized, (
        "Expected the luks_device module DOCUMENTATION for option 'label' to include "
        "the reviewed phrasing 'with label support, respectively to identify the container by' "
        "(whitespace normalized). This verifies the style fix in the docs."
    )