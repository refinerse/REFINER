import pytest


def test_dmp_sqf_norm_docstring_uses_correct_ring_notation_Kxy_kxy():
    """
    Functional-ish test via docstring content: the review fixes the example text
    to use K[x,y] and k[x,y] (multivariate), not K[x] and k[x].

    This has no runtime behavior impact, so we assert on the module docstring
    text of dmp_sqf_norm.
    """
    import sympy.polys.sqfreetools as sqf

    doc = sqf.dmp_sqf_norm.__doc__ or ""
    assert "K[x,y]" in doc and "k[x,y]" in doc, (
        "dmp_sqf_norm docstring example should describe the rings as "
        "K[x,y] and k[x,y] (multivariate)."
    )