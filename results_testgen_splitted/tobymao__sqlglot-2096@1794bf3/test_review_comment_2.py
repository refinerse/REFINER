import pytest

from sqlglot.expressions import DataType


def test_datatype_build_raises_parseerror_for_unparsable_string_when_udt_false():
    """
    Regression test for DataType.build error semantics:
    - After the change, DataType.build should re-raise ParseError from parse_one
      (not wrap it into ValueError and not rely on returning None).
    - Before the change, ParseError was caught and re-raised as ValueError.
    """
    with pytest.raises(Exception) as excinfo:
        DataType.build("NOT_A_REAL_TYPE_12345", udt=False)

    assert isinstance(
        excinfo.value, ValueError
    ) is False, (
        "DataType.build should not wrap parse failures into ValueError; it should "
        "propagate the underlying ParseError to callers."
    )