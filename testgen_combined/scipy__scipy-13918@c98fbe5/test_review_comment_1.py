import re


def test_poissondisk_public_api_and_gammainc_import():
    source = open("/workspace/scipy/stats/_qmc.py", encoding="utf-8").read()

    assert (
        "class PoissonDisk(QMCEngine)" in source
    ), "Expected PoissonDisk engine class to be defined (renamed from PoissonDisc)."

    assert (
        "class PoissonDisc(QMCEngine)" not in source
    ), "PoissonDisc class name should not remain; public engine should be PoissonDisk."

    # Ensure the new engine is part of the public API list
    assert (
        re.search(r"__all__\s*=\s*\[[^\]]*'PoissonDisk'[^\]]*\]", source, re.S) is not None
    ), "Expected 'PoissonDisk' to be exported in __all__."

    # Ensure gammainc is imported from the stable public namespace
    assert (
        "from scipy.special import gammainc" in source
    ), "Expected gammainc to be imported from scipy.special (not cython_special)."

    assert (
        "from scipy.special.cython_special import gammainc" not in source
    ), "Should not import gammainc from scipy.special.cython_special; use scipy.special."