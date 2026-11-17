def test_release_script_uses_pep440_utils_and_does_not_use_alphaN_pattern():
    source = open("/workspace/scripts/release.py", encoding="utf-8").read()

    # After the fix, the script should rely on PEP 440 utilities rather than a custom
    # semver prerelease pattern like `alpha1`, `alpha2`, ...
    assert (
        "from pep440_version_utils import Version, is_valid_version" in source
    ), "Expected release script to use pep440_version_utils (PEP 440) for version parsing/validation."

    assert (
        "ALPHA_VERSION_PATTERN" not in source
    ), "Expected release script to stop using the semver-style ALPHA_VERSION_PATTERN ('alphaN'); PEP 440 uses 'aN'."

    # After the fix, the code defines prerelease flavors including alpha and rc.
    assert (
        'PRERELEASE_FLAVORS = ("alpha", "rc")' in source
        or "PRERELEASE_FLAVORS = ('alpha', 'rc')" in source
    ), "Expected PRERELEASE_FLAVORS to include ('alpha', 'rc') in the updated release script."