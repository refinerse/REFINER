import pytest

from core.dbt.contracts.graph.unparsed import UnitTestInputFixture, UnitTestFormat
from dbt.exceptions import ParsingError


def test_unit_test_fixture_validation_error_includes_format_value():
    """
    The ParsingError raised for mismatched fixture `rows` vs `format` should include
    the actual format value (e.g. "format csv") to make the message clearer.
    """
    fixture = UnitTestInputFixture(input="seed", rows=[], format=UnitTestFormat.CSV)

    # Support both the pre-change classmethod signature and the post-change instance method.
    if hasattr(fixture, "validate_fixture") and callable(getattr(fixture, "validate_fixture")):
        try:
            with pytest.raises(ParsingError) as excinfo:
                fixture.validate_fixture("given", "my_test")
        except TypeError:
            with pytest.raises(ParsingError) as excinfo:
                type(fixture).validate_fixture(fixture, "given", "my_test")
    else:
        pytest.fail("UnitTestFixture.validate_fixture is missing or not callable")

    msg = str(excinfo.value)
    assert "do not match format" in msg, (
        "Expected ParsingError message to include the base phrase 'do not match format' "
        "when fixture rows type mismatches the declared format."
    )
    assert f"format {fixture.format}" in msg, (
        "Expected ParsingError message to include the actual fixture format value, e.g. "
        f"'format {fixture.format}', to clarify which format was expected."
    )