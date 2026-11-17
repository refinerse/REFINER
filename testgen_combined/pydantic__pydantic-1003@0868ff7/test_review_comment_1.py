import inspect
import os


def test_exclude_none_tests_renamed_for_clarity_and_deduplicated():
    # Some execution harnesses set PYTEST_ADDOPTS to unsupported flags (e.g. --no-header).
    # Since this test file is executed under pytest, clearing this prevents pytest from
    # re-reading invalid options during any internal pytest invocations.
    os.environ["PYTEST_ADDOPTS"] = ""

    import tests.test_edge_cases as edge_cases

    functions = {
        name
        for name, obj in inspect.getmembers(edge_cases, inspect.isfunction)
        if getattr(obj, "__module__", None) == edge_cases.__name__
    }

    assert "test_exclude_none" in functions, "Expected `test_exclude_none` to exist (renamed for clarity)."
    assert (
        "test_exclude_none_dict" not in functions
    ), "Expected confusing `test_exclude_none_dict` to be removed/renamed to `test_exclude_none`."