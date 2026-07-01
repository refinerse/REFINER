import inspect

from sympy.polys.matrices.domainmatrix import DomainMatrix


def test_domainmatrix_qr_has_no_redundant_dfm_branch():
    """
    The qr() implementation should not contain a redundant
    `if isinstance(self.rep, DFM): ... else: ...` branch when both sides call
    the same code. This test enforces that by checking the function source.
    """
    src = inspect.getsource(DomainMatrix.qr)

    assert "if isinstance(self.rep, DFM)" not in src, (
        "DomainMatrix.qr() still contains a redundant DFM type-check branch. "
        "The review requested removing this unnecessary if/else when both "
        "branches execute the same code."
    )