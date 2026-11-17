import re


def test_maybe_cast_result_dtype_avoids_top_level_pandas_import():
    """
    The reviewed change removes a top-level `import pandas as pd` from
    pandas/core/dtypes/cast.py and instead performs local imports inside
    maybe_cast_result_dtype.

    This test enforces that to avoid importing pandas (and triggering heavy/fragile
    import-time side effects) when importing this module.
    """
    source = open("/workspace/pandas/core/dtypes/cast.py", encoding="utf-8").read()

    assert (
        "import pandas as pd" not in source
    ), "cast.py should not import pandas at module import time; use local imports instead."

    # Ensure we really are checking the intended updated implementation
    assert (
        "def maybe_cast_result_dtype" in source
    ), "Expected maybe_cast_result_dtype to exist in cast.py"

    assert re.search(
        r"def maybe_cast_result_dtype[\s\S]*?from pandas\.core\.arrays\.boolean import BooleanDtype",
        source,
    ), (
        "maybe_cast_result_dtype should use a local import of BooleanDtype "
        "(from pandas.core.arrays.boolean import BooleanDtype)."
    )
    assert re.search(
        r"def maybe_cast_result_dtype[\s\S]*?from pandas\.core\.arrays\.integer import Int64Dtype",
        source,
    ), (
        "maybe_cast_result_dtype should use a local import of Int64Dtype "
        "(from pandas.core.arrays.integer import Int64Dtype)."
    )

    # And ensure we are not relying on pd.BooleanDtype / pd.Int64Dtype
    assert (
        "isinstance(dtype, pd.BooleanDtype)" not in source
    ), "maybe_cast_result_dtype should not reference pd.BooleanDtype; it should use BooleanDtype."
    assert (
        "return pd.Int64Dtype()" not in source
    ), "maybe_cast_result_dtype should not return pd.Int64Dtype(); it should return Int64Dtype()."