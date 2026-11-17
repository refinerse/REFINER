import re


def test_vm_filter_form_does_not_expose_manufacturer_filter():
    """
    The VirtualMachineFilterForm is a *list filter* form. The review comment requires that we do
    not add a manufacturer_id filter (FR scope is edit forms only), because it would be confusing
    and have no effect on VM filtering.

    This test enforces that:
    - VirtualMachineFilterForm.fieldsets does NOT list 'manufacturer_id'
    - VirtualMachineFilterForm does NOT declare a manufacturer_id form field
    """
    source = open("/workspace/netbox/virtualization/forms/filtersets.py", "r", encoding="utf-8").read()

    # Extract just the VirtualMachineFilterForm class body to avoid false positives from other classes/files.
    m = re.search(
        r"\nclass\s+VirtualMachineFilterForm\b[\s\S]*?\nclass\s+VMInterfaceFilterForm\b",
        source,
        flags=re.MULTILINE,
    )
    assert m, "Could not locate VirtualMachineFilterForm class block in /workspace/netbox/virtualization/forms/filtersets.py"
    vm_form_block = m.group(0)

    assert "manufacturer_id" not in vm_form_block, (
        "VirtualMachineFilterForm should not include a manufacturer_id list filter field or reference it in fieldsets. "
        "The review comment notes there is no manufacturer_id filter for VMs and list filters should not be changed."
    )