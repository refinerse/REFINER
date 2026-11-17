import re


def test_image_image_mode_documentation_mentions_pillow_modes_and_link():
    """
    Verifies the documentation update requested in the review comment:
    the `image_mode` parameter docs should reference Pillow's supported modes
    and include the Pillow concepts link.
    """
    source = open("/workspace/gradio/components/image.py", "r", encoding="utf-8").read()

    # Must include the Pillow link in the `image_mode:` doc line.
    assert (
        "image_mode:" in source
    ), "Expected `image_mode:` to be documented in Image.__init__ docstring."
    assert (
        "https://pillow.readthedocs.io/en/stable/handbook/concepts.html" in source
    ), (
        "Expected `image_mode` documentation to reference Pillow image modes via the "
        "Pillow concepts link, per review comment."
    )

    # Also ensure the `image_mode` doc line explicitly points readers to other modes.
    # (This distinguishes the 'after' docstring from the 'before' version.)
    pattern = re.compile(
        r"image_mode:\s*\"RGB\".*\"L\".*See\s+https://pillow\.readthedocs\.io/en/stable/handbook/concepts\.html",
        re.DOTALL,
    )
    assert pattern.search(source), (
        "Expected `image_mode` parameter documentation to mention RGB/L and add a "
        '"See https://pillow.readthedocs.io/en/stable/handbook/concepts.html" note '
        "about other supported image modes."
    )