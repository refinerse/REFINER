import pytest

from src.sqlfluff.rules.L019 import Rule_L019


def test_l019_following_segment_helper_does_not_silently_return_none():
    """Regression test for L019: following-segment helper must not return None.

    Before: _follows_seg() returned None when there was no next segment.
    After: _get_following_seg() should raise (ValueError per intent; IndexError
    is also acceptable as "not None" / not silent).
    """
    # Avoid BaseRule __init__ requirements by constructing without __init__.
    rule = object.__new__(Rule_L019)

    seg = object()
    raw_stack = (seg,)

    if hasattr(rule, "_get_following_seg"):
        with pytest.raises((ValueError, IndexError)):
            rule._get_following_seg(raw_stack, seg)
    else:
        res = rule._follows_seg(raw_stack, seg)
        assert (
            res is not None
        ), "Before-fix bug: helper returned None for missing following segment (silent failure)."