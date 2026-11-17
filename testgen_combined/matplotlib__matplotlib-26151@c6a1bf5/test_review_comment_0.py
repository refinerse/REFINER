import importlib

import pyparsing


def test_mathtext_pyparsing_version_guard_uses_numeric_tuple_comparison():
    """
    Ensure the pyparsing version guard in mathtext does not use lexicographic
    string comparison (which would misorder e.g. '10.0.0' vs '3.0.0').

    This is a style/robustness check; runtime behavior depends on pyparsing's
    installed version, so we validate the implementation by source inspection.
    """
    # Functional preflight: module must remain importable.
    importlib.import_module("lib.matplotlib._mathtext")

    source = open("/workspace/lib/matplotlib/_mathtext.py", encoding="utf-8").read()

    assert (
        "if pyparsing_version < '3.0.0':" not in source
    ), (
        "mathtext should not compare pyparsing versions as strings "
        "(lexicographic comparison can break for versions like '10.0.0' or "
        "date-based versions)."
    )

    assert (
        "tuple(int(x) for x in pyparsing_version.split(\".\")) < (3, 0, 0)" in source
        or "tuple(int(x) for x in pyparsing_version.split('.')) < (3, 0, 0)" in source
    ), (
        "Expected mathtext to guard pyparsing features using numeric tuple comparison, "
        "e.g. tuple(int(x) for x in pyparsing_version.split('.')) < (3, 0, 0)."
    )

    # Sanity: pyparsing is present and provides a version string.
    assert isinstance(pyparsing.__version__, str) and pyparsing.__version__, (
        "Test assumption failed: pyparsing.__version__ should be a non-empty string."
    )