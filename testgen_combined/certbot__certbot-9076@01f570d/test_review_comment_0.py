import re


def test_finish_release_defines_and_uses_fetch_version_number():
    source = open("/workspace/tools/finish_release.py", "r", encoding="utf-8").read()

    # The review fix introduces a dedicated function to retrieve the version from Azure Pipelines
    # and uses it in main() to ensure `version` is defined before calling promote_snaps(version).
    assert "def fetch_version_number" in source, (
        "finish_release.py should define a helper like fetch_version_number() to retrieve the "
        "release version (fixes crash where `version` was undefined)."
    )

    # Ensure main assigns version from this helper (behavioral wiring of the fix).
    # This checks that the script no longer relies on an undefined `version` variable.
    assert re.search(r"\bversion\s*=\s*fetch_version_number\s*\(\s*\)", source), (
        "main() should set `version = fetch_version_number()` so `version` is defined before "
        "calling promote_snaps(version)."
    )

    # Extra guard: verify promote_snaps is called with version (the point of fetching it).
    assert re.search(r"promote_snaps\s*\(\s*version\s*\)", source), (
        "Expected main() to call promote_snaps(version) using the version fetched from Azure."
    )