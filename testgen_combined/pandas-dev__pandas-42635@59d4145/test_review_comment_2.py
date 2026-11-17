import inspect

import pandas.tests.tools.test_to_datetime as mod


def test_monotonic_increasing_index_test_is_parameterized_over_cache():
    """
    Functional check of the review request: the test added in
    /workspace/pandas/tests/tools/test_to_datetime.py must be parameterized over
    cache=True/False, which manifests at runtime as a function argument named
    'cache' in test_to_datetime_monotonic_increasing_index.

    This fails on the "before" version where the test took no arguments,
    and passes on the "after" version where it accepts 'cache' and is
    parametrized.
    """
    assert hasattr(
        mod, "test_to_datetime_monotonic_increasing_index"
    ), "Expected test_to_datetime_monotonic_increasing_index to exist in pandas.tests.tools.test_to_datetime"

    fn = mod.test_to_datetime_monotonic_increasing_index
    sig = inspect.signature(fn)

    assert "cache" in sig.parameters, (
        "Expected test_to_datetime_monotonic_increasing_index to accept a 'cache' "
        "argument (parameterized over cache=True/False per review comment). "
        f"Got signature: {sig}"
    )
    assert sig.parameters["cache"].default is inspect._empty, (
        "Expected 'cache' to be a required test parameter (provided by parametrize), "
        f"not to have a default. Got signature: {sig}"
    )