import re


def test_iceberg_tests_no_redundant_pyarrow_version_guard_in_test_write_basic():
    """
    The review comment "This is not necessary anymore, right?" refers to removing
    the redundant runtime guard that returned early for pyarrow < 9.0.0 inside
    test_write_basic (the test already has a skipif for pyarrow < 14.0.0).
    """
    path = "/workspace/python/ray/data/tests/test_iceberg.py"
    source = open(path, "r", encoding="utf-8").read()

    # Extract the body of test_write_basic (from its def line up to the next top-level def/if).
    m = re.search(
        r"^def test_write_basic\(\):(?P<body>.*?)(?=^\S|\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert m, f"Expected to find a top-level function 'test_write_basic' in {path}"
    body = m.group("body")

    assert (
        "_get_pyarrow_version" not in body
    ), (
        "test_write_basic should not contain the redundant pyarrow version guard "
        "(calls to _get_pyarrow_version / parse_version with early return). "
        "It should rely on the pytest.mark.skipif condition instead."
    )
    assert (
        "Iceberg only works with PyArrow 9 or above" not in body
    ), (
        "test_write_basic should not include the obsolete comment/guard "
        "about PyArrow 9+, since the test is already skip-gated by PyArrow>=14."
    )