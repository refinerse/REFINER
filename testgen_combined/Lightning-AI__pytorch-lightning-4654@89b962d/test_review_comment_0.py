import importlib
import sys


def test_utilities_init_does_not_expose_is_colab_flag():
    # Ensure we load the currently installed/checked-out version fresh
    sys.modules.pop("pytorch_lightning.utilities", None)
    mod = importlib.import_module("pytorch_lightning.utilities")

    assert not hasattr(
        mod, "IS_COLAB"
    ), "pytorch_lightning.utilities must not define/export an `IS_COLAB` flag (it was requested to be removed)."