import re


def test_whatsnew_0252_does_not_mention_qcut_bool_handling_in_other_section():
    """
    Review requested: move item to 1.0 and be more direct ("boolean input").
    In 0.25.2 this specific bullet should not be present anymore.
    """
    path = "/workspace/doc/source/whatsnew/v0.25.2.rst"
    source = open(path, encoding="utf-8").read()

    # Before: "- :func:`qcut` now handles bool ndarray/Series (:issue:`20303`)"
    # After: the bullet is removed from v0.25.2.
    assert ":issue:`20303`" not in source, (
        "v0.25.2 whatsnew should not include the qcut boolean-handling item "
        "tracked by issue 20303; it should be moved to 1.0 per review comment."
    )

    assert re.search(r"qcut", source) is None, (
        "v0.25.2 whatsnew should not mention qcut in the reviewed bullet; "
        "the qcut boolean-handling note should be absent from this file."
    )