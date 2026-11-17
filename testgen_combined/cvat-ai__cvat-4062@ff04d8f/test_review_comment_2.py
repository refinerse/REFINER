import re


def test_convert_ellipse_uses_separate_rx_ry_assignments_for_readability():
    source = open(
        "/workspace/cvat/apps/dataset_manager/formats/transformations.py",
        "r",
        encoding="utf-8",
    ).read()

    # The review comment requests not using multiple expressions in one line like:
    #   rx, ry = rightX - cx, cy - topY
    # Instead, use two separate assignments:
    #   rx = rightX - cx
    #   ry = cy - topY
    #
    # Since importing the module fails in this environment (cv2 may be missing),
    # we verify this via source inspection.

    assert (
        "rx, ry = rightX - cx, cy - topY" not in source
    ), "Expected EllipsesToMasks.convert_ellipse to avoid multi-assignment 'rx, ry = ...' for readability."

    rx_pattern = re.compile(r"^\s*rx\s*=\s*rightX\s*-\s*cx\s*$", re.MULTILINE)
    ry_pattern = re.compile(r"^\s*ry\s*=\s*cy\s*-\s*topY\s*$", re.MULTILINE)

    assert rx_pattern.search(source), (
        "Expected a separate assignment line 'rx = rightX - cx' in "
        "EllipsesToMasks.convert_ellipse."
    )
    assert ry_pattern.search(source), (
        "Expected a separate assignment line 'ry = cy - topY' in "
        "EllipsesToMasks.convert_ellipse."
    )