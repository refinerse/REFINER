import re


def test_ipam_models_import_order_style():
    """
    Enforce the import style requested in review:
        from ipam.models import ASN, IPAddress, RIR
    (alphabetical order by imported name)

    This is a pure style check via source inspection because importing this
    Django test module requires configured settings in this execution env.
    """
    source = open("/workspace/netbox/dcim/tests/test_filtersets.py").read()

    # Find the specific ipam.models import line (ignoring whitespace variations).
    m = re.search(r"^[ \t]*from[ \t]+ipam\.models[ \t]+import[ \t]+(.+?)\s*$", source, flags=re.M)
    assert m, (
        "Expected /workspace/netbox/dcim/tests/test_filtersets.py to contain a "
        "'from ipam.models import ...' line, but none was found."
    )

    imported_part = m.group(1).strip()
    assert imported_part == "ASN, IPAddress, RIR", (
        "Import style regression: expected the ipam.models import to be exactly\n"
        "    from ipam.models import ASN, IPAddress, RIR\n"
        f"but found:\n    from ipam.models import {imported_part}\n"
        "Keep imported names in alphabetical order."
    )