import inspect

import torchvision.transforms.autoaugment as autoaugment


def test_autoaugment_pil_mode_docstrings_expect_rgb_only():
    # This review comment is about a behavior/documentation contract change for PIL inputs:
    # "If img is PIL Image, it is expected to be in mode 'RGB'."
    #
    # There is no runtime validation in these classes for PIL mode, so we verify the public
    # contract via their docstrings (runtime-accessible via inspect.getdoc).
    for cls in (autoaugment.AutoAugment, autoaugment.RandAugment, autoaugment.TrivialAugmentWide):
        doc = inspect.getdoc(cls) or ""
        assert 'If img is PIL Image, it is expected to be in mode "RGB".' in doc, (
            f"{cls.__name__} docstring should state that PIL inputs are expected to be in mode "
            f'"RGB" only, but it did not. Current docstring:\n{doc}'
        )
        assert 'mode "L" or "RGB"' not in doc, (
            f"{cls.__name__} docstring should no longer claim that PIL mode 'L' is supported, "
            f"but it still does. Current docstring:\n{doc}"
        )