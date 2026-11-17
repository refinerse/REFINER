import importlib


def test_tests_utils_test_data_no_toolz_test_and_no_toolz_imports():
    """
    The review comment marks `tests.utils.test_data.test_toolz` for removal.
    Verify that the module no longer exposes that test and no longer imports
    toolz-related compatibility symbols.
    """
    mod = importlib.import_module("tests.utils.test_data")

    assert not hasattr(
        mod, "test_toolz"
    ), "Expected `tests.utils.test_data.test_toolz` to be removed per review comment."

    # Functional/runtime check: ensure toolz compatibility functions are not imported
    assert not hasattr(
        mod, "pipe"
    ), "Expected `pipe` not to be imported into `tests.utils.test_data` after removing toolz-dependent test."
    assert not hasattr(
        mod, "curry"
    ), "Expected `curry` not to be imported into `tests.utils.test_data` after removing toolz-dependent test."