import inspect

from manim.mobject.mobject import Mobject


def test_mobject_set_has_no_deprecation_rename_comment_in_signature_line():
    """
    Regression test for removal of an in-line comment added to Mobject.set().

    The review comment requests that the comment about renaming/deprecating `.set`
    should be removed because the method is expected to remain.
    """
    source_line = inspect.getsource(Mobject.set)
    assert (
        "renamed" not in source_line
        and "depricated" not in source_line
        and "standerd libary" not in source_line
        and "flake error" not in source_line
    ), (
        "Mobject.set() should not contain an in-line comment suggesting it be "
        "renamed/deprecated; the comment should be removed."
    )