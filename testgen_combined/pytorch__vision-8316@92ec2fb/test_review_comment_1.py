import re


def test_jpeg_correctness_note_is_affirmation():
    source = open("/workspace/test/test_transforms_v2.py", "r", encoding="utf-8").read()

    # The review requested changing the NOTE into an affirmation:
    # "this will fail if torchvision and Pillow use different JPEG encoder/decoder"
    expected_note = "# NOTE: this will fail if torchvision and Pillow use different JPEG encoder/decoder"
    assert (
        expected_note in source
    ), f"Expected updated NOTE comment to be present exactly as:\n{expected_note}\n"

    # Ensure the old, tentative NOTE is gone (it was phrased as a question and didn't mention decoder).
    old_note_pattern = re.compile(r"# NOTE:\s*this may fail if torchvision and Pillow use different JPEG encoder\??")
    assert (
        old_note_pattern.search(source) is None
    ), "Old NOTE comment ('this may fail ... encoder?') should have been replaced with the affirmed wording."