import re


def test_gitpackage_incorporate_comment_reflects_and_semantics():
    source = open("/workspace/core/dbt/task/deps.py").read()

    # This review was about the intended boolean logic: warn_unpinned should be
    # False if either side is False (AND), not "if one is True, make both be True."
    #
    # The runtime logic line stayed as `and` in both versions, so we must assert
    # on the corrected in-code comment that documents the intended behavior.
    assert (
        "# if one is False, make both be False." in source
    ), (
        "Expected GitPackage.incorporate() to document the intended warn_unpinned "
        "merge behavior as AND semantics ('if one is False, make both be False.'). "
        "The prior comment ('if one is True, make both be True.') contradicts the "
        "actual logic and should be corrected."
    )

    # Ensure the incorporate method still uses AND (not OR), matching the author's intent.
    assert re.search(
        r"def incorporate\(self, other\):[\s\S]*?warn_unpinned\s*=\s*self\.warn_unpinned\s*and\s*other\.warn_unpinned",
        source,
    ), (
        "Expected GitPackage.incorporate() to compute warn_unpinned using AND "
        "(self.warn_unpinned and other.warn_unpinned), so that a single False "
        "disables warnings for the merged dependency."
    )