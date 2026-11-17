import re


def test_moment_center_tests_use_pytest_parametrize():
    """
    Review comment asks to avoid repetition by using pytest.mark.parametrize.

    The updated code should replace the old repetitive `test_moment_center`
    with parametrized tests:
      - test_moment_center_scalar_moment
      - test_moment_center_array_moment
    and should include explicit @pytest.mark.parametrize decorators.
    """
    path = "/workspace/scipy/stats/tests/test_stats.py"
    source = open(path, "r", encoding="utf-8").read()

    assert "def test_moment_center(" not in source, (
        "Expected the repetitive `def test_moment_center(self):` test to be "
        "replaced by parametrized tests using `pytest.mark.parametrize`."
    )

    # Check presence of the new parametrized test functions.
    assert "def test_moment_center_scalar_moment" in source, (
        "Expected a new test `test_moment_center_scalar_moment` to exist "
        "and be parametrized with `pytest.mark.parametrize`."
    )
    assert "def test_moment_center_array_moment" in source, (
        "Expected a new test `test_moment_center_array_moment` to exist "
        "and be parametrized with `pytest.mark.parametrize`."
    )

    # Ensure the new tests are actually decorated with parametrize.
    # (Simple regex: look for a parametrize decorator in the few lines above.)
    def _has_parametrize_decorator(func_name: str) -> bool:
        m = re.search(rf"(^|\n)(?P<block>(?:[ \t]*@.*\n)+)[ \t]*def {re.escape(func_name)}\b",
                      source)
        if not m:
            return False
        block = m.group("block")
        return "@pytest.mark.parametrize" in block

    assert _has_parametrize_decorator("test_moment_center_scalar_moment"), (
        "Expected `test_moment_center_scalar_moment` to use one or more "
        "`@pytest.mark.parametrize` decorators to reduce repetition."
    )
    assert _has_parametrize_decorator("test_moment_center_array_moment"), (
        "Expected `test_moment_center_array_moment` to use one or more "
        "`@pytest.mark.parametrize` decorators to reduce repetition."
    )