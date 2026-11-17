import re


def test_siteform_does_not_override_init_or_save_for_m2m_asns():
    """
    The review comment indicates custom __init__ and save() are not necessary for handling
    the reverse of the M2M field (asns). After the fix, SiteForm should NOT define these
    methods (default ModelForm behavior should be used).

    This test inspects the source to ensure SiteForm has no custom __init__ or save.
    """
    source = open("/workspace/netbox/dcim/forms/models.py").read()

    # Extract just the SiteForm class body (up to the next top-level class definition)
    m = re.search(
        r"(?ms)^class\s+SiteForm\b.*?:\n(.*?)(?=^class\s+|\Z)",
        source,
    )
    assert m, "Could not locate SiteForm class definition in /workspace/netbox/dcim/forms/models.py"
    siteform_body = m.group(1)

    assert "def __init__(" not in siteform_body, (
        "SiteForm should not override __init__() to manually set M2M initial values or hide fields; "
        "the review comment indicates this is unnecessary."
    )
    assert re.search(r"(?m)^\s*def\s+save\s*\(", siteform_body) is None, (
        "SiteForm should not override save() to call instance.asns.set(...); "
        "the review comment indicates this should not be necessary."
    )