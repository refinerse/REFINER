import inspect

import sympy.polys.sqfreetools as sqfreetools


def test_dmp_sqf_norm_docstring_mentions_univariate_trager_case():
    """
    Regression test for a documentation fix:
    dmp_sqf_norm is a *multivariate* generalization of Trager76's sqfr_norm,
    which is proved in the *univariate* case. The docstring should say
    "univariate", not "multivariate", in the "See Also" entry for dup_sqf_norm.
    """
    doc = inspect.getdoc(sqfreetools.dmp_sqf_norm) or ""

    assert (
        "Analogous function for univariate polynomials" in doc
    ), (
        "dmp_sqf_norm docstring should describe dup_sqf_norm as 'Analogous "
        "function for univariate polynomials', reflecting that dup_* is the "
        "univariate variant."
    )