import numpy as np
import pytest

from sklearn.preprocessing import PolynomialFeatures


def test_polynomial_features_degree0_include_bias_false_error_message():
    """degree=0 with include_bias=False should raise a clear ValueError.

    This checks that the error message matches the updated wording ("would result in
    an empty output array.") rather than the older wording ("will result to an empty
    dataframe.").
    """
    X = np.array([[1.0, 2.0], [3.0, 4.0]])

    with pytest.raises(ValueError) as excinfo:
        PolynomialFeatures(degree=0, include_bias=False).fit(X)

    msg = str(excinfo.value)
    expected = "Setting degree to zero and include_bias to False would result in an empty output array."
    assert expected in msg, (
        "Expected PolynomialFeatures(degree=0, include_bias=False).fit(X) to raise "
        "ValueError with the updated message about an 'empty output array'. "
        f"Got: {msg!r}"
    )