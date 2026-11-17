import inspect

import tests.test_route53domains.test_route53domains_domain as mod


def test_no_early_return_in_hosted_zone_creation_test():
    """
    The review comment requests rewriting the hosted-zone check to use an assert
    (membership check) rather than returning early from the test.

    This test enforces that the specific test function no longer contains a
    `return` statement.
    """
    fn = getattr(mod, "test_register_domain_creates_hosted_zone", None)
    assert fn is not None, (
        "Expected the updated test function `test_register_domain_creates_hosted_zone` "
        "to exist in `tests.test_route53domains.test_route53domains_domain`."
    )

    src = inspect.getsource(fn)
    assert "return" not in src, (
        "Expected `test_register_domain_creates_hosted_zone` to avoid early `return` "
        "statements and instead use an assertion (e.g., membership check). "
        "Found a `return` in the function source."
    )