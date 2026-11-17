import re


def test_palette_png_is_converted_to_grayscale_when_channels_1():
    source = open("/workspace/test/test_image.py", "r", encoding="utf-8").read()

    # The review changed semantics: when requesting channels=1 ("L"), palette ("P") PNGs
    # must ALSO be converted (via Pillow .convert("L")), i.e. the special-case skip is removed.
    #
    # Before code had:
    #   if not (pil_mode == "L" and img.mode == "P") and pil_mode is not None:
    #       # Don't grayscale palette images
    #       img = img.convert(pil_mode)
    #
    # After code has:
    #   if pil_mode is not None:
    #       img = img.convert(pil_mode)

    forbidden_skip_pattern = r"not\s*\(\s*pil_mode\s*==\s*['\"]L['\"]\s*and\s*img\.mode\s*==\s*['\"]P['\"]\s*\)"
    assert not re.search(forbidden_skip_pattern, source), (
        "Palette ('P') PNG images should not be special-cased to skip conversion to grayscale when "
        "channels=1. The test expects the palette-skip condition "
        "`not (pil_mode == 'L' and img.mode == 'P')` to be removed from /workspace/test/test_image.py."
    )

    assert "# Don't grayscale palette images" not in source, (
        "The comment and logic indicating palette images should not be converted to grayscale should be removed. "
        "With channels=1, palette PNGs must be converted to 'L' like other modes."
    )