import pytest

import torchvision.transforms.v2._augment as augment


def test_jpeg_quality_setup_is_inlined_not_module_level_function():
    """
    The review requested inlining the short helper into JPEG.__init__ rather than keeping
    a standalone module-level function. This test asserts that the module no longer
    exposes the helper.
    """
    assert not hasattr(
        augment, "_setup_quality"
    ), "Expected JPEG quality setup to be inlined into JPEG.__init__ (no module-level _setup_quality helper)."