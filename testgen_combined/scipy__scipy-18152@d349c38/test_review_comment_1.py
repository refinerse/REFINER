import re


def test_moment_center_uses_assert_allclose_not_assert_approx_equal():
    source_path = "/workspace/scipy/stats/tests/test_stats.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Functional intent of the review comment: in the newly-added moment(center=...)
    # tests, use np.testing.assert_allclose (imported as assert_allclose) rather than
    # assert_approx_equal. The "after" code does this with a tight atol.
    assert "def test_moment_center_scalar_moment" in source, (
        "Expected the updated, parametrized moment(center=...) test to be present "
        "(test_moment_center_scalar_moment)."
    )

    # Find the body of the scalar-moment test (keep it simple/robust: regex slice)
    m = re.search(
        r"def test_moment_center_scalar_moment\(.*?\):(?P<body>.*?)(?:\n\s*def |\n\s*@)",
        source,
        flags=re.S,
    )
    assert m is not None, (
        "Could not locate the body of test_moment_center_scalar_moment in "
        f"{source_path}."
    )
    body = m.group("body")

    assert "assert_allclose(" in body, (
        "The moment(center=...) scalar-moment test should use assert_allclose "
        "(per review comment)."
    )
    assert "assert_approx_equal(" not in body, (
        "The moment(center=...) scalar-moment test should not use assert_approx_equal; "
        "use assert_allclose instead (per review comment)."
    )