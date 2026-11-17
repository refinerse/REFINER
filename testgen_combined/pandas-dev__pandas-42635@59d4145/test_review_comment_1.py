import inspect

import pandas.tests.tools.test_to_datetime as mod


def test_test_to_datetime_monotonic_increasing_index_is_simplified_and_deterministic():
    """
    The reviewed change simplified the test data and made the test deterministic:
    - it should parametrize over cache=True/False
    - it should use a fixed start Timestamp("1980") (not datetime.now())
    - it should use deterministic sampling (random_state=1)
    - it should call to_datetime(..., cache=cache)
    """
    src = inspect.getsource(mod.test_to_datetime_monotonic_increasing_index)

    assert "@pytest.mark.parametrize" in src and "cache" in src, (
        "Expected test_to_datetime_monotonic_increasing_index to be parametrized over "
        "cache=True/False after the review."
    )
    assert 'Timestamp("1980")' in src or "Timestamp('1980')" in src, (
        "Expected test_to_datetime_monotonic_increasing_index to use a fixed "
        "Timestamp('1980') start after the review (not datetime.now())."
    )
    assert "datetime.now" not in src, (
        "Expected test_to_datetime_monotonic_increasing_index to not depend on "
        "datetime.now() after the review, to avoid non-determinism."
    )
    assert "random_state=1" in src, (
        "Expected deterministic sampling with random_state=1 in "
        "test_to_datetime_monotonic_increasing_index after the review."
    )
    assert "to_datetime" in src and "cache=cache" in src, (
        "Expected test_to_datetime_monotonic_increasing_index to call "
        "to_datetime(..., cache=cache) after the review."
    )