import re


def test_siteform_asn_help_text_mentions_asn_model_not_many_to_many():
    source = open("/workspace/netbox/dcim/forms/models.py", "r", encoding="utf-8").read()

    # Extract the help_texts entry for 'asn' specifically.
    m = re.search(r"help_texts\s*=\s*\{(?P<body>.*?)\n\s*\}", source, flags=re.DOTALL)
    assert m, "Expected to find a 'help_texts = {...}' dict in /workspace/netbox/dcim/forms/models.py"

    body = m.group("body")
    m_asn = re.search(r"'asn'\s*:\s*([\"'])(?P<text>.*?)(\1)\s*,?", body, flags=re.DOTALL)
    assert m_asn, "Expected help_texts to contain an 'asn' entry"

    asn_help = " ".join(m_asn.group("text").split()).lower()

    assert "asn model" in asn_help, (
        "The SiteForm 'asn' help text should describe deprecation in terms users understand, "
        "e.g. 'in favour of the ASN model' (not 'many-to-many')."
    )
    assert "many-to-many" not in asn_help, (
        "The SiteForm 'asn' help text should not mention 'many-to-many' terminology."
    )