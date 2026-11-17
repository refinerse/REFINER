import pytest

from sklearn.utils.validation import _num_samples


def test_num_samples_fit_attribute_checked_with_builtin_callable():
    """_num_samples should only treat objects as estimators if x.fit is callable.

    Regression test for using `hasattr(x.fit, "__call__")` instead of `callable(x.fit)`:
    some non-callable objects (e.g. numpy arrays) expose a "__call__" attribute that is
    set to None, which incorrectly triggered the estimator TypeError in the old code.
    """

    class HasFitAttrButNotCallableAndLen:
        def __init__(self):
            # numpy.ndarray has an attribute "__call__" (value None), so:
            # - hasattr(x.fit, "__call__") is True  -> buggy behavior raises TypeError
            # - callable(x.fit) is False            -> correct behavior returns len(x)
            import numpy as np

            self.fit = np.array([1, 2, 3])

        def __len__(self):
            return 3

    x = HasFitAttrButNotCallableAndLen()

    # Ensure we are actually exercising the edge-case difference:
    assert hasattr(
        x.fit, "__call__"
    ), "Test setup error: x.fit must have a '__call__' attribute to trigger the old bug."
    assert (
        x.fit.__call__ is None
    ), "Test setup error: x.fit.__call__ should be None (non-callable) for this regression."
    assert not callable(
        x.fit
    ), "Test setup error: x.fit must not be callable so callable(x.fit) is False."

    n = _num_samples(x)
    assert n == 3, "Expected _num_samples to return len(x) when x.fit is not callable."