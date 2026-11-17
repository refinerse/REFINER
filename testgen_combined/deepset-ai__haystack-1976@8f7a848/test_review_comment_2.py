import re


def test_convert_from_transformers_device_accepts_str_or_torch_device():
    source = open("/workspace/haystack/modeling/conversion/transformers.py", "r", encoding="utf-8").read()

    # Ensure we're checking the right function signature area.
    assert "def convert_from_transformers(" in source, "Expected Converter.convert_from_transformers to exist."

    # The style change requested: allow `device` to be `Union[str, torch.device]` (user-facing convenience).
    # Before: `device: torch.device,`
    # After:  `device: Union[str, torch.device],`
    assert (
        "device: Union[str, torch.device]" in source
    ), "Expected convert_from_transformers to annotate device as Union[str, torch.device] to support string devices (e.g. 'cpu', 'cuda') as well as torch.device."

    # Make sure we did not leave the old annotation behind in the signature.
    signature_block = re.search(
        r"def convert_from_transformers\([\s\S]*?\):",
        source,
        flags=re.MULTILINE,
    )
    assert signature_block, "Could not locate convert_from_transformers signature block for validation."
    assert (
        "device: torch.device" not in signature_block.group(0)
    ), "convert_from_transformers signature still uses device: torch.device; it should accept Union[str, torch.device]."