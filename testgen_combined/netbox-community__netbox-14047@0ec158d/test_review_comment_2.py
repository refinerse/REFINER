import re

def test_vm_platform_uses_advanced_selector_and_no_manufacturer_field():
    source = open("/workspace/netbox/virtualization/forms/model_forms.py").read()

    # The FR should be addressed by enabling the advanced selector widget on the platform field
    assert re.search(r"\bplatform\s*=\s*DynamicModelChoiceField\s*\(", source), (
        "Expected VirtualMachineForm to define a 'platform = DynamicModelChoiceField(...)' field."
    )

    # Ensure platform field uses selector=True (advanced selector widget)
    assert re.search(
        r"\bplatform\s*=\s*DynamicModelChoiceField\s*\((?s:.*?)\bselector\s*=\s*True\b(?s:.*?)(\)|,)",
        source
    ), (
        "Expected VirtualMachineForm.platform DynamicModelChoiceField to enable the advanced selector widget "
        "via 'selector=True'."
    )

    # The review comment explicitly says not to add a separate manufacturer field
    assert not re.search(r"\bmanufacturer\s*=\s*DynamicModelChoiceField\s*\(", source), (
        "Did not expect VirtualMachineForm to add a separate 'manufacturer' DynamicModelChoiceField; "
        "the platform field should use the advanced selector instead."
    )

    # Ensure we are not using manufacturer-based query_params filtering for platform anymore
    assert not re.search(
        r"\bplatform\s*=\s*DynamicModelChoiceField\s*\((?s:.*?)\bquery_params\s*=\s*\{(?s:.*?)manufacturer_id(?s:.*?)\}",
        source
    ), (
        "Did not expect VirtualMachineForm.platform to be filtered by a separate manufacturer field "
        "(e.g., query_params containing 'manufacturer_id'). Use selector=True instead."
    )

    # Also ensure the removed pattern isn't present (per @user2 note)
    assert "initial_params" not in source, (
        "Did not expect use of 'initial_params' in this form module; per review guidance, use 'selector=True'."
    )