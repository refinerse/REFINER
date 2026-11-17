import re


def test_ipam_models_import_order_and_asn_position():
    """
    Enforce the reviewed import style change:
    - BEFORE: from ipam.models import IPAddress, Prefix, Service, VLAN, ASN
    - AFTER:  from ipam.models import ASN, IPAddress, Prefix, Service, VLAN
    """
    source = open("/workspace/netbox/dcim/views.py").read()

    # Locate the exact ipam.models import line (single line import in this file).
    m = re.search(r"^from ipam\.models import (.+)$", source, flags=re.MULTILINE)
    assert m, "Expected netbox/dcim/views.py to contain a 'from ipam.models import ...' statement"

    import_list = m.group(1).strip()
    assert import_list == "ASN, IPAddress, Prefix, Service, VLAN", (
        "Expected ipam.models import list to be ordered with ASN first to match review suggestion:\n"
        "    from ipam.models import ASN, IPAddress, Prefix, Service, VLAN\n"
        f"but found:\n"
        f"    from ipam.models import {import_list}"
    )