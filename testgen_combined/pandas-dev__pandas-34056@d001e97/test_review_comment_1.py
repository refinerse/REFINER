import re


def test_maybe_cast_result_dtype_avoids_pd_import_and_uses_local_dtype_imports():
    source = open("/workspace/pandas/core/dtypes/cast.py", encoding="utf-8").read()

    # Ensure there is no module-level "import pandas as pd"
    assert (
        "import pandas as pd" not in source
    ), "cast.py should not import pandas as pd at module scope; prefer direct imports."

    # Extract the whole function, including docstring and indented body.
    # The previous regex only captured the docstring (because it stopped at the
    # first blank line). Here we capture until the next top-level def.
    func_pat = re.compile(
        r"^def maybe_cast_result_dtype\(dtype: DtypeObj, how: str\) -> DtypeObj:\n"
        r"(?P<body>(?:^[ \t].*\n)*)"
        r"(?=^(?:def |class |\Z))",
        re.MULTILINE,
    )
    m = func_pat.search(source)
    assert m is not None, "Could not locate maybe_cast_result_dtype function in cast.py"
    body = m.group("body")

    # After version: local imports inside the function
    assert (
        "from pandas.core.arrays.boolean import BooleanDtype" in body
    ), "maybe_cast_result_dtype should import BooleanDtype locally to avoid using pd.*"
    assert (
        "from pandas.core.arrays.integer import Int64Dtype" in body
    ), "maybe_cast_result_dtype should import Int64Dtype locally to avoid using pd.*"

    # After version: no pd.* references in this function
    assert (
        "pd.BooleanDtype" not in body and "pd.Int64Dtype" not in body
    ), "maybe_cast_result_dtype should not reference pd.BooleanDtype/pd.Int64Dtype; use direct imports."