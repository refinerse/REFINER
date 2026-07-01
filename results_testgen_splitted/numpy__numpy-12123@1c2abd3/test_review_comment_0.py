import pytest
import numpy as np


def test_asscalar_deprecation_warning_mentions_deprecated_since_version():
    a = np.array([24])

    with pytest.warns(DeprecationWarning) as rec:
        out = np.asscalar(a)

    assert out == 24, "np.asscalar should still return the scalar value via a.item()."

    msg = str(rec[0].message)
    assert (
        "deprecated since" in msg and "v1.16" in msg
    ), (
        "Deprecation warning for np.asscalar should mention the version where it was "
        "deprecated (fixed reference), e.g. 'deprecated since NumPy v1.16', rather "
        "than a planned removal version which may change. "
        f"Got warning message: {msg!r}"
    )