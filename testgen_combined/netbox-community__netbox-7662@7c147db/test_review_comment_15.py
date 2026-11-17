import re


def test_asn_csv_form_does_not_explicitly_declare_asn_field():
    """
    The review comment requires that ASN be inferred from the model, i.e. the form
    should not explicitly declare `asn = IntegerField()` (or any explicit `asn = ...`)
    inside ASNCSVForm.
    """
    source = open("/workspace/netbox/ipam/forms/bulk_import.py", encoding="utf-8").read()

    # Extract the body of ASNCSVForm (everything up to the next top-level class definition)
    m = re.search(
        r"^class\s+ASNCSVForm\(.*?\):\n(?P<body>.*?)(?=^\s*class\s+\w+\(|\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert m is not None, "Expected to find class ASNCSVForm in bulk_import.py"

    body = m.group("body")

    # BEFORE code includes: "asn = IntegerField()"
    # AFTER code removes explicit field declaration so `asn` comes from the model via Meta.fields.
    assert not re.search(r"^\s*asn\s*=\s*.+$", body, flags=re.MULTILINE), (
        "ASNCSVForm should not explicitly declare an `asn` form field (e.g. `asn = IntegerField()`); "
        "it should be inferred from the ASN model."
    )