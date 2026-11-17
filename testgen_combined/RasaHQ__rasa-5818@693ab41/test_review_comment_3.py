import re


def test_release_script_supports_rc_prerelease_and_uses_pep440_utils():
    source = open("/workspace/scripts/release.py", encoding="utf-8").read()

    assert (
        "pep440_version_utils" in source
    ), "release script should use pep440_version_utils (PEP 440) to support prereleases like 'rc'"

    assert re.search(
        r"PRERELEASE_FLAVORS\s*=\s*\([^\)]*'rc'|PRERELEASE_FLAVORS\s*=\s*\([^\)]*\"rc\"",
        source,
        flags=re.MULTILINE,
    ), "release script should define PRERELEASE_FLAVORS including 'rc'"

    assert re.search(
        r"elif\s+version\s*==\s*[\"']rc[\"']\s*:",
        source,
        flags=re.MULTILINE,
    ), "parse_next_version should explicitly handle the 'rc' keyword (e.g. X.YrcN) via an 'elif version == \"rc\"' branch"

    assert (
        "next_release_candidate" in source
    ), "release script should use Version.next_release_candidate() for 'rc' versions (PEP 440 style)"