import re


def test_request_password_reset_redirect_url_validation_uses_shared_validator_and_new_description():
    source = open("/workspace/saleor/graphql/account/mutations/base.py").read()

    # Functional intent of the review:
    # - use shared validate_storefront_url(redirect_url) instead of ad-hoc parsing/validate_host
    # - update redirect_url description wording ("URL ..." not "Url ...") and reference RFC 1808
    assert "validate_storefront_url(redirect_url)" in source, (
        "RequestPasswordReset.perform_mutation should validate redirect_url using the shared "
        "validate_storefront_url(redirect_url) helper."
    )

    # Ensure old inline validation is gone (urlparse + validate_host + settings.ALLOWED_STOREFRONT_HOSTS)
    assert "validate_host" not in source, (
        "RequestPasswordReset should not use django.http.request.validate_host directly; "
        "it should rely on validate_storefront_url()."
    )
    assert "urlparse(" not in source, (
        "RequestPasswordReset should not parse redirect_url with urlparse inline; "
        "it should rely on validate_storefront_url()."
    )
    assert "ALLOWED_STOREFRONT_HOSTS" not in source, (
        "RequestPasswordReset should not reference settings.ALLOWED_STOREFRONT_HOSTS in this mutation; "
        "it should rely on validate_storefront_url()."
    )

    # Check that redirect_url argument description was reworded to start with "URL ..."
    # and still mentions RFC 1808.
    m = re.search(r"redirect_url\s*=\s*graphene\.String\([\s\S]*?description=\(\s*([\s\S]*?)\s*\),",
                  source)
    assert m, "Could not find redirect_url graphene.String(...) definition with a description tuple."
    description_block = m.group(1)

    assert "URL of a view where users should be redirected to" in description_block, (
        "redirect_url description should be reworded to: "
        "'URL of a view where users should be redirected to reset the password.'"
    )
    assert "URL in RFC 1808 format" in description_block, (
        "redirect_url description should mention: 'URL in RFC 1808 format.'"
    )