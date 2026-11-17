import inspect

import torchvision.transforms.autoaugment as autoaugment


def test_autoaugment_docstrings_expect_rgb_for_pil_images():
    """
    The review change is a documentation/contract change: PIL images are expected to be RGB (not "L" or "RGB").
    This has no reliable runtime effect, so we assert on the public class docstrings at runtime.
    """
    expected_line = 'If img is PIL Image, it is expected to be in mode "RGB".'
    old_phrase = 'mode "L" or "RGB"'

    for cls in (autoaugment.AutoAugment, autoaugment.RandAugment, autoaugment.TrivialAugmentWide):
        doc = inspect.getdoc(cls) or ""
        assert expected_line in doc, (
            f"{cls.__name__} docstring should specify PIL images are expected to be RGB only. "
            f"Missing line: {expected_line!r}\n"
            f"Actual docstring:\n{doc}"
        )
        assert old_phrase not in doc, (
            f"{cls.__name__} docstring should not claim PIL images can be grayscale ('L'). "
            f"Found disallowed phrase {old_phrase!r}.\n"
            f"Actual docstring:\n{doc}"
        )