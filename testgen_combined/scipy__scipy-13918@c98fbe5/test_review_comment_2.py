import re


def test_poisson_disk_exposes_radius_parameter_and_public_name():
    source = open("/workspace/scipy/stats/_qmc.py", "r", encoding="utf-8").read()

    # The review comment requested that the minimum distance between samples
    # (radius) be a parameter of the sampler. The fix introduced a new public
    # class name PoissonDisk and added a keyword-only `radius` argument.
    #
    # Before: class PoissonDisc(...) with hardcoded self.radius = 0.05
    # After:  class PoissonDisk(...) with __init__(..., *, radius=0.05, ...)
    assert "class PoissonDisk(QMCEngine):" in source, (
        "Expected a public PoissonDisk engine class to exist (renamed/added in "
        "the fix). The pre-fix code used PoissonDisc instead."
    )

    assert re.search(
        r"class\s+PoissonDisk\s*\(QMCEngine\)\s*:[\s\S]*?"
        r"def\s+__init__\s*\([\s\S]*?\*\s*,[\s\S]*?\bradius\s*:\s*[^=]+=\s*0\.05",
        source,
    ), (
        "Expected PoissonDisk.__init__ to accept a keyword-only `radius` "
        "parameter with default 0.05, making the minimum distance configurable."
    )

    # Ensure the previous hardcoded radius assignment in the old class does not
    # remain as the only behavior.
    assert "self.radius = 0.05" not in source, (
        "Expected radius not to be hardcoded as `self.radius = 0.05`; it should "
        "come from the `radius` parameter."
    )

    # Ensure it is exported publicly via __all__
    assert re.search(r"__all__\s*=\s*\[[\s\S]*'PoissonDisk'[\s\S]*\]", source), (
        "Expected 'PoissonDisk' to be included in __all__ so it is publicly "
        "available as scipy.stats.qmc.PoissonDisk."
    )