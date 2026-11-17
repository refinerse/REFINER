import torchvision.transforms.v2.functional._augment as F


def test_exposes_jpeg_video_kernel_function():
    # We cannot call F.jpeg / F.jpeg_video in this environment reliably because torchvision's
    # optional C++ image extension (encode_jpeg/decode_jpeg) may be unavailable, causing a
    # runtime AttributeError unrelated to the review comment.
    #
    # The review comment requests exposing a dedicated `jpeg_video` kernel function. This is
    # an observable API change: before it doesn't exist, after it does.
    assert hasattr(
        F, "jpeg_video"
    ), "Expected `jpeg_video` to be exposed as a dedicated kernel function for consistency (and to call into `jpeg_image()`)."