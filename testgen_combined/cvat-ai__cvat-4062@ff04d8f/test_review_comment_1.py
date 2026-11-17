import re


def test_ellipses_to_masks_uses_opencv_not_pil():
    """
    The review change replaces PIL.ImageDraw-based ellipse rasterization with OpenCV (cv2.ellipse)
    for performance. Since importing the module fails when cv2 isn't installed in this environment,
    we assert on the source code contents directly.
    """
    source = open("/workspace/cvat/apps/dataset_manager/formats/transformations.py", "r", encoding="utf-8").read()

    assert "cv2.ellipse" in source, (
        "Expected EllipsesToMasks.convert_ellipse to use OpenCV (cv2.ellipse) after the change, "
        "but 'cv2.ellipse' was not found in transformations.py"
    )

    forbidden_patterns = [
        r"from\s+PIL\s+import\s+Image\s*,\s*ImageDraw",
        r"\bImageDraw\.Draw\(",
        r"\bdrawer\.ellipse\(",
        r"\bImage\.new\(",
    ]
    for pat in forbidden_patterns:
        assert re.search(pat, source) is None, (
            "Expected PIL-based ellipse drawing to be removed after switching to OpenCV, "
            f"but found pattern {pat!r} in transformations.py"
        )