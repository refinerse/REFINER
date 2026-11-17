import re


def test_ipam_models_import_order_and_members():
    """
    Enforce the style change from the review comment:
    Use `from ipam.models import ASN, VLAN, RIR` (alphabetical within that import)
    instead of `from ipam.models import VLAN, ASN, RIR`.
    """
    source = open("/workspace/netbox/dcim/tests/test_views.py").read()

    # Find the ipam.models import line (single-line import expected here)
    m = re.search(r"(?m)^\s*from\s+ipam\.models\s+import\s+([^\n#]+)", source)
    assert m is not None, (
        "Expected an import from 'ipam.models' in /workspace/netbox/dcim/tests/test_views.py, "
        "but none was found."
    )

    imported = m.group(1).strip()

    assert imported == "ASN, VLAN, RIR", (
        "Style: expected ipam.models imports to be ordered as 'ASN, VLAN, RIR' "
        f"but found: '{imported}'."
    )