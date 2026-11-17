import torch


def test_jpeg_image_uses_view_not_reshape_for_flatten_and_restore():
    """
    Structural regression test:
    The review requested using `.view` (not `.reshape`) to avoid unintended copies when flattening/restoring.
    This has no reliable runtime behavioral difference, so we verify the implementation via source inspection.
    """
    source = open("/workspace/torchvision/transforms/v2/functional/_augment.py", "r", encoding="utf-8").read()

    # Ensure the jpeg_image function exists
    assert "def jpeg_image" in source, "Expected `jpeg_image` to be defined in _augment.py"

    # Check that flattening uses view, not reshape
    assert (
        "image = image.view((-1,) + image.shape[-3:])" in source
    ), "Expected `jpeg_image` to flatten with `image.view((-1,) + image.shape[-3:])` (no copy) rather than `reshape`."

    # Check that restoring shape after stack also uses view, not reshape
    assert (
        "torch.stack(image, dim=0).view(original_shape)" in source
    ), "Expected `jpeg_image` to restore with `.view(original_shape)` rather than `.reshape(original_shape)`."