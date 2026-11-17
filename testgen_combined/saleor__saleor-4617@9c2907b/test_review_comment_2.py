import re


def test_validate_storefront_url_handles_urlparse_valueerror_with_validationerror():
    source = open("/workspace/saleor/core/utils/url.py").read()

    assert "def validate_storefront_url(url):" in source, (
        "Expected saleor/core/utils/url.py to define validate_storefront_url(url)."
    )

    # The review comment indicates urlparse can raise ValueError and should be handled.
    # Verify the implementation wraps urlparse in try/except ValueError and raises ValidationError.
    assert re.search(r"try:\s*\n\s*parsed_url\s*=\s*urlparse\(url\)", source), (
        "validate_storefront_url(url) should wrap `parsed_url = urlparse(url)` in a try block "
        "to handle ValueError from urlparse."
    )
    assert re.search(r"except\s+ValueError\s+as\s+\w+:\s*\n\s*raise\s+ValidationError\(", source), (
        "validate_storefront_url(url) should catch ValueError from urlparse and re-raise it as "
        "django.core.exceptions.ValidationError."
    )
    assert '{"redirectUrl":' in source or "{'redirectUrl':" in source, (
        "When re-raising as ValidationError, the error should be associated with the "
        "'redirectUrl' field (e.g., ValidationError({'redirectUrl': str(error)}))."
    )