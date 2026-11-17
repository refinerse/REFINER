import re


def _extract_test_gels_block(source: str) -> str:
    """
    Extract the body of TestLeastSquaresSolvers.test_gels as a substring.

    We intentionally keep this simple and robust (no AST parsing), and we scope
    checks to this function so unrelated uses of lwork patterns elsewhere in
    the file don't affect the test.
    """
    # Find the "def test_gels" that is inside TestLeastSquaresSolvers
    m = re.search(
        r"(?ms)^class\s+TestLeastSquaresSolvers\(TestCase\):\s*\n(.*?)(?=^class\s|\Z)",
        source,
    )
    assert m is not None, "Could not locate class TestLeastSquaresSolvers(TestCase) in the file."
    cls_block = m.group(1)

    m2 = re.search(
        r"(?ms)^\s+def\s+test_gels\s*\(self\)\s*:\s*\n(.*?)(?=^\s+def\s|\Z)",
        cls_block,
    )
    assert m2 is not None, "Could not locate method test_gels(self) inside TestLeastSquaresSolvers."
    return m2.group(0)


def test_gels_uses_compute_lwork_and_keyword_lwork():
    source = open("/workspace/scipy/linalg/tests/test_lapack.py", "r", encoding="utf-8").read()
    gels_block = _extract_test_gels_block(source)

    # Check the refactor requested in the review: use _compute_lwork and lwork= keyword.
    assert (
        re.search(r"from\s+scipy\.linalg\.lapack\s+import\s+_compute_lwork", source)
        is not None
    ), (
        "Expected 'from scipy.linalg.lapack import _compute_lwork' to be present "
        "to follow the review request."
    )

    assert (
        "_compute_lwork(gels_lwork" in gels_block
    ), "Expected test_gels to compute lwork via _compute_lwork(gels_lwork, m, n, nrhs)."

    assert (
        re.search(r"\bgels\([^)]*lwork\s*=\s*lwork", gels_block) is not None
    ), "Expected test_gels to call gels(..., lwork=lwork) using the keyword argument."

    # Ensure test_gels no longer uses the old manual workspace query pattern.
    assert (
        re.search(r"work\s*,\s*info\s*=\s*gels_lwork\(\s*m\s*,\s*n\s*,\s*nrhs\s*\)", gels_block)
        is None
    ), (
        "Old style detected in test_gels: manual 'work, info = gels_lwork(m, n, nrhs)' "
        "should be replaced by '_compute_lwork(...)'."
    )

    assert (
        "lwork = int(np.real(work))" not in gels_block
    ), (
        "Old style detected in test_gels: 'lwork = int(np.real(work))' should not be used "
        "after switching to _compute_lwork."
    )