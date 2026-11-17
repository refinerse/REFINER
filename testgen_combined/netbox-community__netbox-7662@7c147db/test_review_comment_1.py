import re


def test_siteform_does_not_hide_deprecated_asn_field_in_init():
    """
    The review comment requested keeping the deprecated `asn` field visible in the form
    (help text explains deprecation) and avoiding dynamic removal/hiding logic in __init__.
    """
    source = open("/workspace/netbox/dcim/forms/models.py", "r", encoding="utf-8").read()

    # Ensure we're looking at the correct form/class in this file
    assert "class SiteForm" in source, "Expected to find SiteForm in /workspace/netbox/dcim/forms/models.py"

    # The "before" code added an __init__ that deletes/hides the deprecated `asn` field and edits fieldsets.
    # After the change, that __init__ (and especially deletion of self.fields['asn']) should be absent.
    assert "del self.fields['asn']" not in source, (
        "SiteForm should not dynamically remove the deprecated 'asn' field from the form. "
        "Per review comment, keep it present and rely on help text to explain deprecation."
    )

    # Also guard against the specific comment/logic indicating this behavior.
    assert "Hide the ASN field" not in source, (
        "SiteForm should not contain logic/comment to hide the deprecated 'asn' field; "
        "it should remain in the form as documented."
    )

    # Sanity: the deprecated ASN help text should still exist to explain deprecation.
    # (Allow either wording variant shown in before/after snippets.)
    assert re.search(r"'asn'\s*:\s*\"BGP autonomous system number\.", source), (
        "Expected SiteForm Meta.help_texts to document deprecation for the 'asn' field."
    )