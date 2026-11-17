import inspect

import bin.coverage_doctest as cd


def test_indirect_doctest_parameter_names_are_spelled_correctly():
    """
    The review comment requires fixing the misspelling "indierect" -> "indirect"
    in variable/parameter names. This is observable at runtime via function
    signatures.
    """
    sig = inspect.signature(cd.print_coverage)
    params = list(sig.parameters)

    assert "c_indirect_doctest" in params, (
        "print_coverage should accept parameter 'c_indirect_doctest' "
        "(spelled 'indirect'), not a misspelled variant."
    )
    assert "f_indirect_doctest" in params, (
        "print_coverage should accept parameter 'f_indirect_doctest' "
        "(spelled 'indirect'), not a misspelled variant."
    )
    assert all("indierect" not in p for p in params), (
        "No parameter name in print_coverage should contain the misspelling "
        "'indierect'."
    )

    sig_pf = inspect.signature(cd.process_function)
    pf_params = list(sig_pf.parameters)
    assert "f_indirect_doctest" in pf_params, (
        "process_function should accept parameter 'f_indirect_doctest' "
        "(spelled 'indirect'), not a misspelled variant."
    )
    assert all("indierect" not in p for p in pf_params), (
        "No parameter name in process_function should contain the misspelling "
        "'indierect'."
    )

    sig_pc = inspect.signature(cd.process_class)
    pc_params = list(sig_pc.parameters)
    assert "c_indirect_doctest" in pc_params, (
        "process_class should accept parameter 'c_indirect_doctest' "
        "(spelled 'indirect'), not a misspelled variant."
    )
    assert all("indierect" not in p for p in pc_params), (
        "No parameter name in process_class should contain the misspelling "
        "'indierect'."
    )