import re


def test_precommit_black_language_version_pinned_to_python38():
    source = open("/workspace/.pre-commit-config.yaml", "r", encoding="utf-8").read()

    # Ensure we're checking the correct hook block (avoid matching other occurrences).
    # Look for the black repo section and verify the black hook pins python to 3.8.
    pattern = re.compile(
        r"""
        -\s*repo:\s*https://github\.com/ambv/black\s*\n
        (?:[^\n]*\n)*?                 # non-greedy: consume lines in this repo block
        \s*-\s*id:\s*black\s*\n
        \s*language_version:\s*(?P<langver>[^\s#]+)
        """,
        re.VERBOSE,
    )

    m = pattern.search(source)
    assert m, (
        "Expected to find the black pre-commit hook configuration in "
        "/workspace/.pre-commit-config.yaml, but it was not found."
    )

    langver = m.group("langver")
    assert langver == "python3.8", (
        "The code review requested pinning black's pre-commit hook to Python 3.8. "
        f"Expected `language_version: python3.8` under the black hook, but found "
        f"`language_version: {langver}`."
    )