import re


def test_no_redundant_asn_import_present():
    """
    Style check: Ensure netbox/ipam/filtersets.py does not include a redundant
    explicit import of ASN (e.g., `from .models import ASN`) since the module
    already imports all models via `from .models import *`.

    This test MUST fail on the "before" code (which includes `from .models import ASN`)
    and pass on the "after" code (which omits it).
    """
    source = open("/workspace/netbox/ipam/filtersets.py", "r", encoding="utf-8").read()

    # Match as a standalone import line (allowing whitespace).
    redundant_import = re.search(r"(?m)^\s*from\s+\.models\s+import\s+ASN\s*$", source)

    assert redundant_import is None, (
        "Redundant explicit import found: `from .models import ASN`. "
        "Since this file already does `from .models import *`, the explicit ASN import "
        "should be removed to satisfy the style change."
    )