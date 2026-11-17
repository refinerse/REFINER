import re


def test_poissondisk_exposes_tunable_candidate_parameter_and_name():
    source = open("/workspace/scipy/stats/_qmc.py", "r", encoding="utf-8").read()

    # The review comment requested that the hard-coded `k=30` / `self.k = 30`
    # be made tunable via a parameter, and that a better name be used.
    #
    # We assert for the concrete, user-visible API: PoissonDisk(..., ncandidates=30, ...)
    # and the internal attribute `self.ncandidates = ncandidates`.
    #
    # BEFORE: class PoissonDisc with hard-coded `self.k = 30` (no parameter)
    # AFTER:  class PoissonDisk with parameter `ncandidates` defaulting to 30.

    assert "class PoissonDisk" in source, (
        "Poisson disk engine should be exposed as class `PoissonDisk` "
        "(renamed from PoissonDisc as part of the API changes)."
    )

    # Ensure the tunable parameter exists in __init__ with default 30.
    assert re.search(r"\bncandidates\s*:\s*IntNumber\s*=\s*30\b", source), (
        "PoissonDisk.__init__ should accept a tunable `ncandidates` parameter "
        "with default value 30 (replacing hard-coded k=30)."
    )

    # Ensure the parameter is actually stored/used (not just documented).
    assert "self.ncandidates = ncandidates" in source, (
        "PoissonDisk should store the tunable number of candidates as "
        "`self.ncandidates = ncandidates`."
    )

    # Ensure we are not still using the old hard-coded attribute name.
    assert "self.k = 30" not in source, (
        "PoissonDisk should not hard-code the number of candidates via "
        "`self.k = 30`; it must be user-tunable."
    )