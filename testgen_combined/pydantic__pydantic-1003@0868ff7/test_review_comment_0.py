import inspect


def test_exclude_none_tests_are_consolidated_without_importing_pytest_or_repo_tests_package():
    """
    The repository's `tests/test_edge_cases.py` imports `pytest` and defines many pytest tests.
    In this execution environment, importing pytest can crash due to extra CLI args being
    injected (e.g. `--no-header`) while running under `pytest -c /dev/null`.

    To keep this test fully self-contained and avoid any pytest initialization, we:
    - read the source file by absolute path
    - strip out the `import pytest` line
    - execute the file in an isolated namespace with a minimal stub `pytest` object
      that provides decorators used at import-time (`mark.parametrize`, `mark.skipif`)
    Then we introspect defined function names to verify redundant tests were consolidated.
    """
    module_path = "/workspace/tests/test_edge_cases.py"
    source = open(module_path, "r", encoding="utf8").read()

    # Remove direct pytest import(s) to prevent pytest from initializing and crashing.
    filtered_lines = []
    for line in source.splitlines(True):
        if line.startswith("import pytest"):
            continue
        filtered_lines.append(line)
    filtered_source = "".join(filtered_lines)

    class _PytestMarkStub:
        @staticmethod
        def parametrize(*args, **kwargs):
            def deco(fn):
                return fn

            return deco

        @staticmethod
        def skipif(*args, **kwargs):
            def deco(fn):
                return fn

            return deco

    class _PytestStub:
        mark = _PytestMarkStub()

    namespace = {
        "__name__": "edge_cases_loaded_for_style_check",
        "__file__": module_path,
        # Provide a stub so `@pytest.mark.parametrize` etc. are valid.
        "pytest": _PytestStub(),
    }

    exec(compile(filtered_source, module_path, "exec"), namespace, namespace)

    functions = {name for name, obj in namespace.items() if inspect.isfunction(obj)}

    assert "test_exclude_none" in functions, "Expected consolidated test function 'test_exclude_none' to exist."

    assert (
        "test_exclude_none_dict" not in functions
    ), "Expected old redundant test 'test_exclude_none_dict' to be removed in favor of 'test_exclude_none'."

    removed_redundant = {
        "test_dict_exclude_none_populated_by_alias",
        "test_dict_exclude_none_populated_by_alias_with_extra",
        "test_dict_exclude_none_populated_with_extra",
    }
    remaining = removed_redundant & functions
    assert not remaining, (
        "Expected redundant exclude_none tests to be removed/merged per review comment; "
        f"still found: {sorted(remaining)}"
    )

    expected_consolidated = {"test_exclude_none_recursive", "test_exclude_none_with_extra"}
    missing = expected_consolidated - functions
    assert not missing, f"Expected consolidated tests to exist; missing: {sorted(missing)}"