import re


def test_request_password_reset_uses_shared_storefront_url_validation_function():
    source = open("/workspace/saleor/graphql/account/mutations/base.py").read()

    # The review asked to extract the storefront URL validation to a reusable function.
    # After the change, base.py should call `validate_storefront_url(redirect_url)`
    # instead of performing inline validation via urlparse/validate_host.
    assert (
        "validate_storefront_url(redirect_url)" in source
    ), (
        "Expected RequestPasswordReset.perform_mutation to call the shared "
        "`validate_storefront_url(redirect_url)` helper (extracted validation), "
        "but it was not found in saleor/graphql/account/mutations/base.py."
    )

    # Ensure the old inline validation approach is gone from this module.
    assert "validate_host(" not in source, (
        "Expected storefront URL validation to be extracted to a helper; found "
        "inline `validate_host(...)` usage in saleor/graphql/account/mutations/base.py."
    )
    assert "urlparse(" not in source, (
        "Expected storefront URL validation to be extracted to a helper; found "
        "inline `urlparse(...)` usage in saleor/graphql/account/mutations/base.py."
    )

    # Bonus: verify the helper is imported from core utils (as suggested by the comment).
    assert re.search(r"from\s+\.\.\.\.core\.utils\.url\s+import\s+validate_storefront_url", source), (
        "Expected `validate_storefront_url` to be imported from `saleor.core.utils.url` "
        "in saleor/graphql/account/mutations/base.py."
    )