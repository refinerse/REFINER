import re


def test_bar_uint8_is_not_image_comparison_and_has_numeric_assertions():
    source = open("/workspace/lib/matplotlib/tests/test_axes.py", encoding="utf-8").read()

    # Locate the definition of the function under review.
    m = re.search(r"(?m)^def test_bar_uint8\(\):\n(?P<body>(?:[ \t].*\n)*)", source)
    assert m is not None, "Expected test_axes.py to define a function named test_bar_uint8()."
    body = m.group("body")

    # 1) The review change removes the image comparison decorator for this test.
    # Check that there is no @image_comparison directly above the function.
    prefix = source[:m.start()]
    last_nonempty = [ln for ln in prefix.splitlines() if ln.strip()][-1]
    assert "@image_comparison" not in last_nonempty, (
        "test_bar_uint8() should not be an image_comparison test anymore; "
        "expected the decorator to be removed and replaced by numeric assertions."
    )

    # 2) The review change adds a numerical check that bars end up at the right x positions.
    assert "assert" in body, (
        "test_bar_uint8() should contain at least one numeric assertion verifying bar placement, "
        "but no 'assert' was found in the function body."
    )
    assert "patch.xy[0]" in body, (
        "test_bar_uint8() should assert bar patch x positions (e.g. 'assert patch.xy[0] == x'); "
        "expected to find 'patch.xy[0]' in the function body."
    )