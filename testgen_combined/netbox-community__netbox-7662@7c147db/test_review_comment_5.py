import re


def _get_asn_field_block(source: str) -> str:
    """
    Extract the argument block inside `asn = ASNField(...)` for the ASN model.
    This avoids importing Django models (settings aren't configured in this test environment).
    """
    # Locate the ASN model
    m_model = re.search(r"\bclass\s+ASN\s*\([^)]*\)\s*:", source)
    assert m_model, "Expected to find `class ASN(...)` definition in ip.py"
    start = m_model.end()

    # Locate the ASNField assignment within the ASN class
    m_field = re.search(r"\basn\s*=\s*ASNField\s*\(", source[start:])
    assert m_field, "Expected to find `asn = ASNField(` inside ASN model definition"
    pos = start + m_field.end()  # points just after the opening parenthesis

    # Extract balanced parentheses content
    depth = 1
    i = pos
    while i < len(source) and depth:
        ch = source[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        i += 1

    assert depth == 0, "Failed to parse `ASNField(...)` argument block (unbalanced parentheses)"
    return source[pos : i - 1]  # content inside ASNField(...)


def test_asn_asnfield_is_required_not_blank_or_null():
    source = open("/workspace/netbox/ipam/models/ip.py").read()

    block = _get_asn_field_block(source)

    assert re.search(r"\bblank\s*=\s*False\b", block), (
        "ASN.asn must be a required form field: expected `blank=False` in `asn = ASNField(...)`"
    )
    assert re.search(r"\bnull\s*=\s*False\b", block), (
        "ASN.asn must be non-nullable in the database: expected `null=False` in `asn = ASNField(...)`"
    )