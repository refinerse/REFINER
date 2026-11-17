import inspect

import core.dbt.contracts.graph.unparsed as unparsed


def test_validate_fixture_is_instance_method_and_no_longer_takes_fixture_param():
    """
    The review change converts validate_fixture from a @classmethod that takes an explicit
    `fixture` argument to an instance method that operates on `self`.

    We assert two runtime-observable properties:
      1) validate_fixture is a bound instance method when accessed on an instance
      2) its signature no longer includes a `fixture` parameter (the key behavioral change)
    """
    fixture = unparsed.UnitTestOutputFixture()

    assert inspect.ismethod(
        fixture.validate_fixture
    ), "validate_fixture should be an instance method (bound on the fixture instance), not a @classmethod"

    sig = inspect.signature(fixture.validate_fixture)

    assert (
        "fixture" not in sig.parameters
    ), "validate_fixture should not accept a separate 'fixture' parameter; it should validate `self`"

    assert list(sig.parameters.keys()) == [
        "fixture_type",
        "test_name",
    ], f"Expected validate_fixture(fixture_type, test_name) on the bound method, got: {sig}"
    assert (
        sig.return_annotation is None
    ), "validate_fixture should have an explicit return type annotation of 'None' (-> None)"