import re


def test_logistic_dtype_match_test_is_not_duplicated_and_ends_cleanly():
    source_path = "/workspace/sklearn/linear_model/tests/test_logistic.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # The "before" version accidentally kept an extra unfinished/duplicated test
    # `test_dtype_missmatch_to_profile` (and had extra trailing blank lines).
    # The "after" version removes it.
    assert (
        "def test_dtype_missmatch_to_profile" not in source
    ), (
        "Found leftover unfinished duplicate test `test_dtype_missmatch_to_profile` in "
        f"{source_path}. It should be removed after addressing the review comment."
    )

    # Also ensure the file ends cleanly (no excessive trailing blank lines).
    # Allow exactly one final newline at EOF.
    assert not re.search(r"\n{3,}\Z", source), (
        f"{source_path} ends with 3+ trailing newlines; it should end cleanly "
        "after addressing the review comment about the extra newline."
    )