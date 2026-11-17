import re


def _extract_test_gels_block(source: str) -> str:
    """
    Extract the source text for the `def test_gels(self):` method only.

    We scope checks to this block because the file legitimately contains other
    least-squares tests (e.g. gelsd/gelss/gelsy) that still use
    `lwork = int(np.real(work))`.
    """
    m = re.search(r"(?ms)^\s*def\s+test_gels\s*\(self\)\s*:\s*(.*?)^\s*def\s+test_gelsd\s*\(self\)\s*:", source)
    assert m is not None, "Could not locate test_gels method block in /workspace/scipy/linalg/tests/test_lapack.py"
    return m.group(0)


def test_gels_uses_compute_lwork_and_geqrf_truth_for_lqr():
    """
    Verify the fix to avoid brittle hard-coded lqr results in test_gels:
    - compute lwork using _compute_lwork
    - compute lqr_truth via geqrf(a1) and compare with assert_array_equal
    """
    source = open("/workspace/scipy/linalg/tests/test_lapack.py", "r", encoding="utf8").read()
    gels_block = _extract_test_gels_block(source)

    # The fix imports _compute_lwork at module scope
    assert "from scipy.linalg.lapack import _compute_lwork" in source, (
        "Expected test_lapack.py to import _compute_lwork (used by test_gels)."
    )

    # test_gels should request geqrf alongside gels and gels_lwork
    assert re.search(r"get_lapack_funcs\([^)]*'geqrf'", gels_block) or re.search(
        r'get_lapack_funcs\([^)]*"geqrf"', gels_block
    ), "Expected test_gels to request 'geqrf' via get_lapack_funcs(...)."

    # lwork should be computed via _compute_lwork in test_gels (not int(real(work)))
    assert re.search(r"\blwork\s*=\s*_compute_lwork\(", gels_block), (
        "Expected test_gels to compute lwork using _compute_lwork(...)."
    )
    assert "lwork = int(np.real(work))" not in gels_block, (
        "test_gels should not compute lwork via int(np.real(work)); use _compute_lwork instead."
    )

    # lqr should be compared to geqrf(a1) output, not hard-coded floats
    assert re.search(r"\blqr_truth\b.*=\s*geqrf\(\s*a1\s*\)", gels_block), (
        "Expected test_gels to compute lqr_truth from geqrf(a1)."
    )
    assert "assert_array_equal(lqr, lqr_truth)" in gels_block, (
        "Expected test_gels to use assert_array_equal(lqr, lqr_truth) rather than "
        "assert_allclose against hard-coded lqr values."
    )

    # Ensure the old hard-coded lqr arrays are not present in test_gels
    assert "assert_allclose(lqr, np.array([[-8.1240384" not in gels_block, (
        "Old real hard-coded lqr array should not appear in test_gels; compare to geqrf instead."
    )
    assert "assert_allclose(lqr," not in gels_block, (
        "test_gels should not assert_allclose(lqr, <hard-coded array>); it should compare to geqrf."
    )