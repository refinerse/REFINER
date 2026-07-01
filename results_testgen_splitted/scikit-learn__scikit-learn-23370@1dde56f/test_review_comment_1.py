import numpy as np
import pytest

from sklearn.preprocessing import PolynomialFeatures


def test_polynomial_features_degree0_include_bias_false_error_message_is_output_array():
    """degree=0 with include_bias=False should raise a ValueError with the new wording."""
    X = np.array([[1.0, 2.0], [3.0, 4.0]])

    with pytest.raises(ValueError) as excinfo:
        PolynomialFeatures(degree=0, include_bias=False).fit(X)

    msg = str(excinfo.value)
    assert (
        "would result in an empty output array" in msg
    ), f"Expected updated error message mentioning 'empty output array', got: {msg!r}"
    assert (
        "empty dataframe" not in msg
    ), f"Old error message ('empty dataframe') should not be used anymore, got: {msg!r}"