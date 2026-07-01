import numpy as np
import pytest

from sklearn.metrics import log_loss, make_scorer


class OneClassProbaClassifier:
    """Classifier whose predict_proba returns only one column (one class)."""

    def predict_proba(self, X):
        # shape (n_samples, 1) mimics a classifier trained on a single class
        return np.ones((len(X), 1), dtype=float)


class OneClassDecisionFunctionClassifier:
    """Classifier without decision_function, forcing ThresholdScorer to use predict_proba."""

    def predict_proba(self, X):
        return np.ones((len(X), 1), dtype=float)


def test_proba_scorer_error_message_includes_predict_proba_shape_and_fix_hint():
    scorer = make_scorer(log_loss, needs_proba=True)
    clf = OneClassProbaClassifier()
    X = np.zeros((3, 2))
    y = np.array([0, 1, 0])  # binary target => scorer expects 2 prob columns

    with pytest.raises(ValueError) as err:
        scorer(clf, X, y)

    msg = str(err.value)
    assert "got predict_proba of shape" in msg, (
        "Error message should mention the actual predict_proba shape to help "
        "debug single-class classifiers. Got: {!r}".format(msg)
    )
    assert "(3, 1)" in msg, (
        "Error message should include the concrete predict_proba shape. "
        "Got: {!r}".format(msg)
    )
    assert "need classifier with two classes" in msg, (
        "Error message should explain how to fix the issue (use a 2-class classifier). "
        "Got: {!r}".format(msg)
    )


def test_threshold_scorer_error_message_includes_predict_proba_shape_and_fix_hint():
    # roc_auc uses needs_threshold=True and will fall back to predict_proba when
    # decision_function is missing.
    from sklearn.metrics import roc_auc_score

    scorer = make_scorer(roc_auc_score, needs_threshold=True)
    clf = OneClassDecisionFunctionClassifier()
    X = np.zeros((4, 2))
    y = np.array([0, 1, 0, 1])

    with pytest.raises(ValueError) as err:
        scorer(clf, X, y)

    msg = str(err.value)
    assert "got predict_proba of shape" in msg, (
        "Threshold-based scorer should also mention predict_proba shape when it "
        "falls back to predict_proba. Got: {!r}".format(msg)
    )
    assert "(4, 1)" in msg, (
        "Error message should include the concrete predict_proba shape. "
        "Got: {!r}".format(msg)
    )
    assert "need classifier with two classes" in msg, (
        "Error message should explain how to fix the issue (use a 2-class classifier). "
        "Got: {!r}".format(msg)
    )