import re


def test_dirichlet_stick_breaking_uses_saved_beta_variate():
    """
    Regression test for Dirichlet stick-breaking bug.

    In the stick-breaking loop, the accumulator must be updated with (1 - v)
    where v is the raw beta variate, not with (1 - val_data[i+j]) where
    val_data[i+j] already includes the factor 'acc'.
    """
    source = open("/workspace/numpy/random/_generator.pyx", "r", encoding="utf-8").read()

    # Ensure we're looking at the intended part of the implementation: the
    # stick-breaking algorithm using random_beta.
    assert "stick-breaking" in source and "random_beta" in source, (
        "Expected stick-breaking Dirichlet implementation using random_beta to be present."
    )

    # The fixed code must:
    # 1) store random_beta(...) into a local variable v
    # 2) write val_data[...] = acc * v
    # 3) update acc *= (1. - v)
    #
    # The buggy code updated using val_data[...] instead of v.
    required_patterns = [
        r"\bv\s*=\s*random_beta\s*\(",
        r"\bval_data\s*\[[^\]]+\]\s*=\s*acc\s*\*\s*v\b",
        r"\bacc\s*\*=\s*\(\s*1\.\s*-\s*v\s*\)",
    ]
    for pat in required_patterns:
        assert re.search(pat, source), (
            "Dirichlet stick-breaking code must save the beta variate in a local "
            f"variable and update accumulator with (1 - v). Missing pattern: {pat!r}"
        )

    assert "acc *= (1. - val_data" not in source, (
        "Dirichlet stick-breaking accumulator must not be updated using val_data[i+j], "
        "because val_data includes multiplication by acc and would distort the distribution."
    )