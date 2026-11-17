import re


def test_vlanfilterset_filter_method_is_not_test_prefixed():
    source = open("/workspace/netbox/ipam/filtersets.py", "r", encoding="utf-8").read()

    # The style fix is specifically about not using a `test_` prefix for a filter method.
    assert "def test_filter_interface_id" not in source, (
        "Found `def test_filter_interface_id(...)` in netbox/ipam/filtersets.py. "
        "FilterSet helper methods must not be named with a `test_` prefix; "
        "it should be `def filter_interface_id(...)`."
    )

    # Ensure the corrected method name exists somewhere in the module.
    # (Don't require a leading newline; it may be indented inside the class.)
    assert re.search(r"\bdef\s+filter_interface_id\s*\(", source), (
        "Expected to find `def filter_interface_id(...)` in netbox/ipam/filtersets.py "
        "after the style fix (method renamed from `test_filter_interface_id`)."
    )