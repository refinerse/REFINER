import pytest
import numpy as np

from sklearn.preprocessing import PolynomialFeatures


def test_degree_tuple_zero_zero_include_bias_false_raises_with_specific_message():
    """Regression test for degree=(0, 0) with include_bias=False.

    The reviewed change added a dedicated ValueError (and message) for the tuple
    form degree=(0, 0). This test asserts that this exact error message is raised.

    This fails on the "before" version because it does *not* raise (it returns an
    empty array instead), and it passes on the "after" version.
    """
    X = np.ones((10, 2))

    poly = PolynomialFeatures(degree=(0, 0), include_bias=False)
    expected_msg = (
        r"Setting both min_deree and max_degree to zero and include_bias to"
        r" False would result in an empty output array\."
    )

    with pytest.raises(ValueError, match=expected_msg):
        poly.fit_transform(X)