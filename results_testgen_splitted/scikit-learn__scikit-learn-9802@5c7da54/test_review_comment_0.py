import pytest

from sklearn.linear_model import SGDClassifier


def test_sgd_classifier_no_set_future_warning_constructor_param():
    """Regression test for review comment:
    'set_future_warning' should not be a constructor parameter; it should be
    handled internally by _validate_params.

    This test asserts that end-user estimators (e.g. SGDClassifier) do not
    accept an unexpected 'set_future_warning' parameter.
    """
    with pytest.raises(TypeError, match=r"set_future_warning"):
        SGDClassifier(set_future_warning=False)

    # Also ensure set_params doesn't accept it either (would reintroduce a
    # public API for this internal knob).
    clf = SGDClassifier()
    with pytest.raises(ValueError, match=r"set_future_warning"):
        clf.set_params(set_future_warning=False)