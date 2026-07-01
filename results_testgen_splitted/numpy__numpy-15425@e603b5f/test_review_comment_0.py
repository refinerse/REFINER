import inspect

import numpy.tests.test_public_api as tpa


def test_test_dir_testing_is_not_parametrized_anymore():
    """
    The reviewed change removes @pytest.mark.parametrize from test_dir_testing,
    turning it into a single test that checks len(dir(np)) == len(set(dir(np))).
    This is a style/API change observable via the test function signature.
    """
    sig = inspect.signature(tpa.test_dir_testing)
    assert (
        len(sig.parameters) == 0
    ), (
        "Expected numpy.tests.test_public_api.test_dir_testing to take no "
        "arguments after the review change (no pytest parametrization). "
        f"Found parameters: {list(sig.parameters)}"
    )