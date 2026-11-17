import pytest

from telegram._utils.markup import check_keyboard_type


def test_check_keyboard_type_does_not_index_into_rows_before_row_type_check():
    """
    Regression test for a bug where check_keyboard_type tried to access keyboard[0][0]
    before validating that rows are sequences.

    For keyboard=[1], the function should *not* raise (e.g. TypeError: 'int' is not subscriptable)
    and should return False because the row is not a sequence.
    """
    keyboard = [1]

    try:
        result = check_keyboard_type(keyboard)
    except Exception as exc:  # noqa: BLE001 - we want to ensure *no* exception is raised
        pytest.fail(
            "check_keyboard_type([1]) must not raise. It should validate row types before "
            f"attempting nested indexing. Raised: {type(exc).__name__}: {exc}"
        )

    assert result is False, "check_keyboard_type([1]) should return False because rows are not sequences."