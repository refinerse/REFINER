import re

def test_ellipses_to_masks_is_not_itemtransform_subclass():
    """
    The review comment requests that EllipsesToMasks should not inherit from ItemTransform.
    Since importing the module fails in this environment (cv2 missing), inspect source text.
    """
    path = "/workspace/cvat/apps/dataset_manager/formats/transformations.py"
    source = open(path, "r", encoding="utf-8").read()

    # Ensure the class exists (avoid false positives if file structure changes)
    assert "class EllipsesToMasks" in source, "Expected EllipsesToMasks class to exist in transformations.py"

    # Key requirement: class definition must not inherit from ItemTransform anymore
    assert not re.search(r"^\s*class\s+EllipsesToMasks\s*\(\s*ItemTransform\s*\)\s*:", source, re.MULTILINE), (
        "EllipsesToMasks should NOT inherit from ItemTransform per review comment; "
        "expected `class EllipsesToMasks:` instead of `class EllipsesToMasks(ItemTransform):`."
    )