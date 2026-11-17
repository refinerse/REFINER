import pytest

from sympy import ZZ, QQ
from sympy.polys.matrices.ddm import DDM
from sympy.polys.matrices.exceptions import DMDomainError


def test_ddm_qr_requires_field_and_uses_exact_division():
    # On the fixed code, qr() should reject non-field domains like ZZ.
    # On the buggy code, it silently proceeds (and also uses //).
    Azz = DDM([[ZZ(2), ZZ(1)], [ZZ(1), ZZ(1)]], (2, 2), ZZ)

    with pytest.raises(DMDomainError, match="requires a field"):
        Azz.qr()

    # On the fixed code, qr() should work over a field (e.g. QQ) and return
    # Q and R with expected shapes: Q is m x min(m,n), R is min(m,n) x n.
    Aqq = DDM([[QQ(2), QQ(1)], [QQ(1), QQ(1)]], (2, 2), QQ)
    Q, R = Aqq.qr()

    assert Q.shape == (2, 2), "Over a field, qr() should return Q with shape (m, min(m,n))."
    assert R.shape == (2, 2), "Over a field, qr() should return R with shape (min(m,n), n)."

    # For a matrix with non-orthogonal columns, Gram-Schmidt should produce
    # a nonzero off-diagonal entry in R, and it must be exact rational division.
    # For this A, R[0,1] should be (q0·a1)/(q0·q0) = 3/5.
    assert R[0][1] == QQ(3, 5), (
        "qr() over QQ should compute R[0,1] using exact field division, "
        "giving 3/5 for this input (not floor division)."
    )