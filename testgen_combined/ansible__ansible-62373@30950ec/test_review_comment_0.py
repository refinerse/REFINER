import inspect

import lib.ansible.plugins.action.__init__ as action_init


def test__is_become_unprivileged_uses_truthiness_check_for_become():
    """
    Style regression test for consistency: _is_become_unprivileged should use
    `if not self._connection.become:` (truthiness) rather than
    `if self._connection.become is None:` (None-only check).
    """
    src = inspect.getsource(action_init.ActionBase._is_become_unprivileged)

    assert "if not self._connection.become" in src, (
        "Expected ActionBase._is_become_unprivileged to use a truthiness check "
        "(`if not self._connection.become:`) for consistency. "
        "This should fail if the code uses a None-only check "
        "(`if self._connection.become is None:`)."
    )

    assert "if self._connection.become is None" not in src, (
        "ActionBase._is_become_unprivileged should not use a None-only check "
        "(`if self._connection.become is None:`); prefer `if not self._connection.become:` "
        "for consistency."
    )