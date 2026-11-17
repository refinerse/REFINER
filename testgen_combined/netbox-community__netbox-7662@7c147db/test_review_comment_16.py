import re


def test_site_bulk_edit_form_retains_single_asn_field():
    """
    The review comment requires keeping the legacy `asn` field on SiteBulkEditForm.
    Verify the SiteBulkEditForm class defines `asn = forms.IntegerField(...)`.
    """
    source = open("/workspace/netbox/dcim/forms/bulk_edit.py", encoding="utf-8").read()

    # Narrow the search to the SiteBulkEditForm class block to avoid false positives
    m = re.search(
        r"(?ms)^\s*class\s+SiteBulkEditForm\b.*?:\s*(?P<body>.*?)(?=^\s*class\s+|\Z)",
        source,
    )
    assert m is not None, "Expected to find class SiteBulkEditForm in bulk_edit.py"

    body = m.group("body")

    assert re.search(r"(?m)^\s*asn\s*=\s*forms\.IntegerField\s*\(", body), (
        "SiteBulkEditForm must retain the legacy `asn` field as a forms.IntegerField; "
        "it was removed/renamed in the pre-fix code."
    )