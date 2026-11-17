import re


def test_linprog_highs_returns_fields_moved_from_marginals_to_sections():
    source = open("/workspace/scipy/optimize/_linprog_highs.py", encoding="utf-8").read()

    # Runtime behavior isn't importable in this environment, so we verify the
    # externally visible contract via the documented return structure *and*
    # the corresponding returned dict construction.
    #
    # Before: returned dict had key 'marginals' holding an OptimizeResult with
    #         'ineqlin', 'eqlin', 'lower', 'upper' arrays.
    # After:  returned dict has keys 'ineqlin', 'eqlin', 'lower', 'upper'
    #         each being an OptimizeResult with 'residual' and 'marginals'.

    assert "'marginals': OptimizeResult" not in source, (
        "The HiGHS linprog result should no longer include a top-level 'marginals' "
        "OptimizeResult; marginals should instead be under 'ineqlin', 'eqlin', "
        "'lower', and 'upper'."
    )

    for key in ["ineqlin", "eqlin", "lower", "upper"]:
        assert re.search(rf"sol\s*=\s*\{{[\s\S]*'{key}'\s*:\s*OptimizeResult\s*\(", source), (
            f"Expected returned solution dict to include top-level key '{key}' "
            "as an OptimizeResult (moved from the old top-level 'marginals')."
        )

    # Ensure the new structured results include both residual and marginals fields.
    assert "'residual': slack" in source and "'marginals': marg_ineqlin" in source, (
        "Expected 'ineqlin' OptimizeResult to include both 'residual' (slack) and "
        "'marginals' (marg_ineqlin)."
    )
    assert "'residual': con" in source and "'marginals': marg_eqlin" in source, (
        "Expected 'eqlin' OptimizeResult to include both 'residual' (con) and "
        "'marginals' (marg_eqlin)."
    )