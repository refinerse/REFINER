import inspect

import torchvision.transforms.v2._augment as augment


def test_jpeg_uses_check_sequence_input_req_sizes_keyword():
    source = inspect.getsource(augment.JPEG.__init__)
    assert "_check_sequence_input" in source, "Sanity check: JPEG.__init__ should validate `quality` via _check_sequence_input()."

    assert "req_sizes=(2,)" in source, (
        "JPEG.__init__ must call _check_sequence_input with the `req_sizes=(2,)` keyword argument. "
        "This is the reviewed change that ensures the helper is invoked with the correct signature."
    )

    assert '_check_sequence_input(quality, "quality", (2,' not in source, (
        "JPEG.__init__ must not pass (2,) positionally to _check_sequence_input (i.e. as the third argument). "
        "That old call uses the wrong parameter (req_len) and was the bug fixed by the review comment."
    )