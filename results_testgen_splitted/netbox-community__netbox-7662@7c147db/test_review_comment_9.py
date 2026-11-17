import re


def test_ipam_api_views_does_not_import_asn_from_parent_models_module():
    """
    Style regression test: ASN should be available via `from ipam.models import *`
    and therefore MUST NOT be imported redundantly as `from ..models import ASN`.
    """
    source = open("/workspace/netbox/ipam/api/views.py", encoding="utf-8").read()

    # Match a standalone import line; tolerate varying whitespace.
    redundant_import_re = re.compile(r"(?m)^\s*from\s+\.\.\s*models\s+import\s+ASN\s*$")

    assert not redundant_import_re.search(source), (
        "Redundant import detected in /workspace/netbox/ipam/api/views.py: "
        "`from ..models import ASN` should be removed (ASN is already imported via "
        "`from ipam.models import *`)."
    )