import re


def _get_asn_class_block(source: str) -> str:
    """
    Return the source substring for the ASN model class definition block.
    """
    m = re.search(r"\nclass\s+ASN\s*\(PrimaryModel\)\s*:\s*\n", source)
    assert m, "Expected to find `class ASN(PrimaryModel):` definition in /workspace/netbox/ipam/models/ip.py"
    start = m.start() + 1  # drop leading newline

    # Find next top-level class definition after ASN
    m2 = re.search(r"\n@extras_features\([^\n]*\)\nclass\s+\w+\s*\(", source[m.end():])
    if not m2:
        # Fallback: next "class <Name>(" at column 0
        m2 = re.search(r"\nclass\s+\w+\s*\(", source[m.end():])

    assert m2, "Expected to find a subsequent class definition after `ASN` to bound the class block"
    end = m.end() + m2.start()

    return source[start:end]


def test_asn_model_has_no_sites_m2m_and_asn_field_is_required():
    source = open("/workspace/netbox/ipam/models/ip.py", "r", encoding="utf-8").read()

    asn_block = _get_asn_class_block(source)

    assert "sites = models.ManyToManyField" not in asn_block, (
        "ASN model should no longer define a `sites = models.ManyToManyField(...)` relationship; "
        "the M2M was moved to the Site model per review comment."
    )

    # Ensure ASN field is required (blank=False, null=False) rather than optional.
    assert "asn = ASNField" in asn_block, "Expected ASN model to define `asn = ASNField(...)`"

    assert "blank=False" in asn_block and "null=False" in asn_block, (
        "ASN.asn field should be required (blank=False, null=False). In the pre-change code it was optional "
        "(blank=True, null=True), which should no longer be the case."
    )