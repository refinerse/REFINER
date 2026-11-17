import inspect

import lib.ansible.plugins.action.__init__ as action_init


def test_configure_module_become_kwargs_does_not_duplicate_modify_module_defaults():
    """
    Style contract: _configure_module should start with `become_kwargs = {}` and only
    populate it when `self._connection.become` is truthy, rather than duplicating
    modify_module defaults like become=False, become_method=None, etc.

    This is a style-only change with no runtime API impact, so we verify via
    straightforward source inspection (no AST parsing).
    """
    source = inspect.getsource(action_init.ActionBase._configure_module)

    assert "become_kwargs = {}" in source, (
        "Expected ActionBase._configure_module to initialize `become_kwargs` as an empty dict "
        "(`become_kwargs = {}`), relying on modify_module defaults unless become is in use."
    )

    assert "'become': False" not in source, (
        "ActionBase._configure_module should not duplicate modify_module defaults like "
        "`'become': False` in `become_kwargs`; it should start empty and only set keys when "
        "`self._connection.become` is truthy."
    )