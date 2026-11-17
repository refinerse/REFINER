import pytest

from manim.mobject.value_tracker import ValueTracker


def test_value_tracker_iadd_mutates_and_returns_self():
    vt = ValueTracker(1.5)
    alias = vt  # simulate another reference that should observe the mutation

    returned = vt.__iadd__(2.0)  # call directly to avoid any bytecode edge cases

    assert (
        returned is vt
    ), "__iadd__ should mutate the existing ValueTracker and return self (not a new instance)."

    assert (
        alias is vt
    ), "Sanity check: alias should still reference the same ValueTracker instance."

    assert alias.get_value() == pytest.approx(
        3.5
    ), "Mutating via __iadd__ should update the value in-place so existing references observe the new value."