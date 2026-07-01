import inspect

import torchvision.transforms.v2._augment as aug


def test_jpeg_docstring_mentions_decompression():
    """
    Review comment requires the JPEG transform docstring to state that it applies
    JPEG compression AND decompression. This is observable at runtime via the class
    __doc__ string.
    """
    doc = inspect.getdoc(aug.JPEG) or ""
    assert (
        "compression and decompression" in doc
    ), f"JPEG transform docstring should mention 'compression and decompression', but got:\n{doc}"