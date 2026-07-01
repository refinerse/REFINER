import pytest

from moto.route53domains.validators import Route53DomainsContactDetail, ValidationException


def test_phone_number_validation_is_liberal_in_allows_variable_length() -> None:
    """
    Regression test for PHONE_NUMBER_REGEX being too strict.

    Route53DomainsContactDetail.validate() should accept phone numbers in the
    expected "+<country>.<number>" format without enforcing an exact length
    of digits after the dot.
    """
    # This is a realistic-ish number that is not 10 digits after the dot
    # (the pre-fix version required exactly 10 digits).
    phone = "+1.1234567"

    try:
        Route53DomainsContactDetail.validate(phone_number=phone)
    except ValidationException as exc:
        pytest.fail(
            "Phone number validation should be liberal and accept variable-length "
            f'phone numbers like "{phone}" in +<country>.<number> format, but got errors: {exc.errors}'
        )