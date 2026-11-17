import re


def test_dtype_match_uses_explicit_float32_and_float64_variables():
    source = open("/workspace/sklearn/linear_model/tests/test_logistic.py").read()

    # The review comment requires explicit float32/float64 variants:
    # X_32 = ...astype(np.float32); X_64 = ...astype(np.float64)
    # (and similarly for y), instead of the ambiguous astype(32)/astype(64)
    # or a single X_ variable.
    assert "def test_dtype_match():" in source, "Expected test_dtype_match to exist."

    # Must define both X_32 and X_64 with explicit numpy float dtypes.
    assert (
        re.search(r"\bX_32\s*=\s*np\.array\(X\)\.astype\(\s*np\.float32\s*\)", source)
        is not None
    ), (
        "test_dtype_match should define X_32 as np.array(X).astype(np.float32) "
        "to ensure float32 inputs are preserved."
    )
    assert (
        re.search(r"\bX_64\s*=\s*np\.array\(X\)\.astype\(\s*np\.float64\s*\)", source)
        is not None
    ), (
        "test_dtype_match should define X_64 as np.array(X).astype(np.float64) "
        "to compare against a true float64 reference."
    )

    # Likewise for y_32 and y_64.
    assert (
        re.search(r"\by_32\s*=\s*np\.array\(Y1\)\.astype\(\s*np\.float32\s*\)", source)
        is not None
    ), (
        "test_dtype_match should define y_32 as np.array(Y1).astype(np.float32)."
    )
    assert (
        re.search(r"\by_64\s*=\s*np\.array\(Y1\)\.astype\(\s*np\.float64\s*\)", source)
        is not None
    ), (
        "test_dtype_match should define y_64 as np.array(Y1).astype(np.float64)."
    )