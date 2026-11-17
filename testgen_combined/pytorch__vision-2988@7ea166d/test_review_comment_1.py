import inspect

import torchvision.io.image as image


def test_decode_jpeg_uses_channels_argument_name_in_python_api():
    sig = inspect.signature(image.decode_jpeg)
    params = list(sig.parameters.values())

    # Expect: decode_jpeg(input: Tensor, channels: int = 0) -> Tensor
    assert len(params) >= 2, (
        "decode_jpeg should accept at least two parameters: (input, channels). "
        f"Got signature: {sig}"
    )
    assert params[1].name == "channels", (
        "Python API should use consistent argument name 'channels' (not 'components') "
        "for decode_jpeg. "
        f"Got signature: {sig}"
    )
    assert params[1].default == 0, (
        "decode_jpeg 'channels' parameter should default to 0 to preserve prior behavior. "
        f"Got signature: {sig}"
    )