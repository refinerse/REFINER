import pytest

from sqlglot.errors import ParseError
from sqlglot.expressions import DataType


def test_datatype_build_unparsable_raises_parseerror_when_udt_false():
    """
    Regression test for DataType.build error behavior:
    - When parsing fails and udt=False (default), the underlying ParseError should be re-raised
      (not converted to ValueError).
    """
    unparsable = "THIS_IS_NOT_A_REAL_TYPE("

    with pytest.raises(
        ParseError,
        match=r".*",
    ) as excinfo:
        DataType.build(unparsable)

    assert isinstance(
        excinfo.value, ParseError
    ), "DataType.build should re-raise ParseError on unparsable dtype when udt=False (default), not wrap it in ValueError."