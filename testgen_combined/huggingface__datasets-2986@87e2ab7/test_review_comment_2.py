import re


def test_canonical_master_fallback_disabled_when_hf_scripts_version_set():
    """
    The review change: for canonical datasets/metrics, fallback to revision="master" should only happen
    if BOTH `revision` and the `HF_SCRIPTS_VERSION` env var are unspecified.

    We can't import datasets due to pyarrow incompatibility in this environment, so we inspect the source.
    """
    source = open("/workspace/src/datasets/load.py", "r", encoding="utf-8").read()

    # We expect the canonical fallback guard to include the env var check:
    #   if revision is not None or os.getenv("HF_SCRIPTS_VERSION", None) is not None:
    #       raise
    #   else:
    #       revision = "master"
    #
    # This must exist at least once (dataset and/or metric factory).
    pattern = re.compile(
        r'os\.getenv\(\s*["\']HF_SCRIPTS_VERSION["\']\s*,\s*None\s*\)\s*is\s+not\s+None',
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "Expected Canonical*ModuleFactory to avoid falling back to 'master' when the user specifies "
        "HF_SCRIPTS_VERSION. Could not find an `os.getenv('HF_SCRIPTS_VERSION', None) is not None` check "
        "in /workspace/src/datasets/load.py."
    )