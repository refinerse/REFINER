import pytest

from torchvision.transforms.v2._augment import JPEG


def test_jpeg_quality_error_message_includes_received_value():
    # Use an invalid quality that will make it through the type/sequence checks in both versions
    # and trigger the final ValueError.
    bad_quality = (0, 101)

    with pytest.raises(ValueError) as excinfo:
        JPEG(quality=bad_quality)

    msg = str(excinfo.value)
    assert "quality must be an integer from 1 to 100" in msg, (
        "JPEG should raise a ValueError with the standard message when quality is invalid."
    )
    assert "got quality" in msg and str(bad_quality) in msg, (
        "Error message should include the received quality value (e.g. 'got quality = (...)') "
        f"to help debugging, but got: {msg!r}"
    )