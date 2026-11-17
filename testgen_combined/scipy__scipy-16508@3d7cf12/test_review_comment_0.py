import re


def test_rgi_nonscalar_values_uses_explicit_atol_1e_14():
    """
    The review comment requests making floating-point equality explicit by adding
    `atol=1e-14` to the assert_allclose in the new RegularGridInterpolator
    test_nonscalar_values.

    This test inspects the source to ensure that specific assert_allclose call
    includes the explicit `atol=1e-14`.
    """
    source = open("/workspace/scipy/interpolate/tests/test_rgi.py", "r", encoding="utf-8").read()

    # Extract the TestRegularGridInterpolator.test_nonscalar_values method body.
    m = re.search(
        r"class\s+TestRegularGridInterpolator\b.*?"
        r"def\s+test_nonscalar_values\s*\(\s*self\s*,\s*method\s*\)\s*:(?P<body>.*?)(?:\n\s*def\s|\nclass\s|\Z)",
        source,
        flags=re.S,
    )
    assert m is not None, (
        "Could not locate TestRegularGridInterpolator.test_nonscalar_values in "
        "/workspace/scipy/interpolate/tests/test_rgi.py; test layout changed."
    )
    body = m.group("body")

    # Find the assert_allclose call that compares v and v2 in that test.
    # Before: assert_allclose(v, v2, err_msg=method)
    # After:  assert_allclose(v, v2, atol=1e-14, err_msg=method)
    call = re.search(r"assert_allclose\s*\(\s*v\s*,\s*v2\s*,(?P<args>[^)]*)\)", body, flags=re.S)
    assert call is not None, (
        "Expected an assert_allclose(v, v2, ...) call in "
        "TestRegularGridInterpolator.test_nonscalar_values."
    )

    args = call.group("args")
    assert re.search(r"\batol\s*=\s*1e-14\b", args) is not None, (
        "Floating-point comparison in TestRegularGridInterpolator.test_nonscalar_values "
        "must specify `atol=1e-14` explicitly (per review comment). "
        f"Found assert_allclose(v, v2, {args.strip()}) without that atol."
    )