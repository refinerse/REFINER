import importlib

import numpy as np


def test_ncx2_zero_nc_reference_values_match_R():
    """
    Ensure the embedded expected values in test_distributions.test_ncx2_zero_nc
    correspond to calling ncx2.{cdf,pdf,logpdf} at x=0.1 (R reference values).

    This should FAIL on the "before" version (which embeds x=1 expected values)
    and PASS on the "after" version.
    """
    td = importlib.import_module("scipy.stats.tests.test_distributions")

    # Extract parametrize data from the function's applied mark.
    mark = td.test_ncx2_zero_nc.pytestmark[0]
    assert mark.name == "parametrize"
    assert mark.args[0] == "method, expected"

    param_list = mark.args[1]
    assert len(param_list) == 3, "Expected 3 parametrized methods: cdf, pdf, logpdf"

    x = 0.1
    df = 10
    nc = [0, 4]

    for method, expected in param_list:
        actual = getattr(td.stats.ncx2, method)(x, nc=nc, df=df)
        assert np.allclose(
            actual, expected, atol=1e-15
        ), (
            f"Expected embedded R reference values for ncx2.{method}(x=0.1, df=10, nc=[0,4]).\n"
            f"Got actual={actual}, embedded expected={expected}."
        )