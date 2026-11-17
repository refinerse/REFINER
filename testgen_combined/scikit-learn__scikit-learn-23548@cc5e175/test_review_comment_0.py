import pytest

import sklearn.metrics.tests.test_ranking as test_ranking


def test_coverage_1d_error_message_parametrized():
    """Ensure the non-regression test for 1d inputs is parametrized.

    This must cover all specified (y_true, y_score) combinations; otherwise the
    test would stop at the first failing call and not execute the remaining
    cases.
    """
    func = getattr(test_ranking, "test_coverage_1d_error_message", None)
    assert callable(func), "Expected test_coverage_1d_error_message to exist and be callable."

    mark = func.pytestmark[0] if getattr(func, "pytestmark", None) else None
    assert mark is not None, (
        "Expected test_coverage_1d_error_message to be decorated with a pytest mark "
        "(specifically pytest.mark.parametrize) to cover multiple 1d input cases."
    )
    assert getattr(mark, "name", None) == "parametrize", (
        "Expected test_coverage_1d_error_message to use pytest.mark.parametrize so that "
        "all 1d input combinations are tested independently."
    )

    # Extract the parametrized cases from the mark and ensure there are 3,
    # matching the intended coverage.
    argnames, argvalues = mark.args[:2]
    assert "y_true" in argnames and "y_score" in argnames, (
        f"Expected parametrization over y_true and y_score; got argnames={argnames!r}."
    )
    assert len(argvalues) == 3, (
        "Expected 3 parametrized (y_true, y_score) cases to be tested; "
        f"got {len(argvalues)}."
    )