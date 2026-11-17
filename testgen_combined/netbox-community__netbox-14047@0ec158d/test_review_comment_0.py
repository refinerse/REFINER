import re


def test_device_filter_form_hardware_fieldset_ordering_is_stable():
    """
    Ensure the DeviceFilterForm "Hardware" fieldset retains the intended ordering:
    manufacturer_id, device_type_id, platform_id.

    This test scopes the search specifically to the DeviceFilterForm class body to
    avoid accidentally matching other forms' "Hardware" fieldsets (e.g. RackFilterForm).
    """
    source = open("/workspace/netbox/dcim/forms/filtersets.py", "r", encoding="utf-8").read()

    # Restrict to the DeviceFilterForm class block (up to the next class definition)
    m_class = re.search(
        r"\nclass\s+DeviceFilterForm\b[\s\S]*?(?=\nclass\s+\w+|\Z)",
        source,
    )
    assert m_class is not None, "Could not locate class DeviceFilterForm block in filtersets.py"
    device_filter_form_block = m_class.group(0)

    # Locate the "Hardware" fieldset tuple within DeviceFilterForm.fieldsets
    m_hw = re.search(
        r"""\(\s*_\(\s*['"]Hardware['"]\s*\)\s*,\s*\(\s*([^)]+?)\s*\)\s*\)""",
        device_filter_form_block,
        flags=re.DOTALL,
    )
    assert m_hw is not None, "Could not find the _('Hardware') fieldset tuple inside DeviceFilterForm.fieldsets"

    # Extract the field names as simple strings (in order)
    hardware_fields = re.findall(r"['\"]([a-z_]+)['\"]", m_hw.group(1))

    assert hardware_fields == ["manufacturer_id", "device_type_id", "platform_id"], (
        "DeviceFilterForm 'Hardware' fieldset should retain the stable ordering "
        "('manufacturer_id', 'device_type_id', 'platform_id'). "
        f"Found ordering: {hardware_fields}"
    )