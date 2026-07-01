import pytest

from sklearn.pipeline import Pipeline


class _FinalEstimatorWithFalseyPredict:
    # Attribute exists but is falsey (None).
    predict = None

    def fit(self, X, y=None):
        return self


def test_available_if_does_not_use_attribute_truthiness():
    """
    Regression test for Pipeline's available_if predicate.

    The predicate used by @available_if(_final_estimator_has("predict")) should
    return True whenever the attribute exists on the final estimator, regardless
    of the attribute's truthiness.

    Before fix: _final_estimator_has returned getattr(..., attr) or True, which
    evaluates to the attribute value when truthy and to True when falsey; for a
    falsey attribute it returns True, but for a truthy attribute it returns the
    attribute itself. In particular, for a falsey attribute it *does not*
    guarantee a strict boolean return value across cases and can be confusing.

    After fix: _final_estimator_has always returns True after verifying the
    attribute exists (raising the original AttributeError otherwise).
    """
    pipe = Pipeline([("final", _FinalEstimatorWithFalseyPredict())])

    # Access the descriptor created by @available_if on the class dict.
    # (Accessing Pipeline.predict directly triggers descriptor binding and
    # returns a function-like object.)
    descriptor = Pipeline.__dict__["predict"]
    predicate = descriptor.check

    result = predicate(pipe)
    assert result is True, (
        "The available_if predicate for Pipeline.predict must return True when "
        "the final estimator has a 'predict' attribute, even if that attribute "
        "is falsey (e.g. None)."
    )