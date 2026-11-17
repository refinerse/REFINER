import re


def test_asn_csv_form_does_not_declare_asn_integerfield():
    """
    Style check: ASNCSVForm should not explicitly declare `asn = IntegerField()`.
    The form should rely on the model field via Meta.fields instead.
    """
    source = open("/workspace/netbox/ipam/forms/bulk_import.py", encoding="utf-8").read()

    # Extract the ASNCSVForm class block up to the next class definition
    m = re.search(
        r"^class\s+ASNCSVForm\b.*?:\n(?P<body>.*?)(?=^class\s+\w+\b|\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert m, "Expected to find class definition for ASNCSVForm in bulk_import.py"

    body = m.group("body")

    assert "asn = IntegerField()" not in body, (
        "ASNCSVForm should not declare `asn = IntegerField()` explicitly. "
        "It should rely on the model field (keep 'asn' in Meta.fields), as in the addressed review."
    )