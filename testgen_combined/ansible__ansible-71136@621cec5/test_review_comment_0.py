import pytest

from lib.ansible.executor.task_executor import TaskExecutor


class _Host:
    def __init__(self, name, address):
        self.name = name
        self.address = address


class _Task:
    def __init__(self, delegate_to):
        self.delegate_to = delegate_to
        self.action = "debug"
        self.args = {}
        self._uuid = "task-uuid"

        # Fields referenced later in _execute() but we won't reach them due to our stubs
        self.loop_with = None
        self.loop = None
        self.loop_control = None
        self.changed_when = None
        self.failed_when = None
        self.register = None
        self.async_val = 0
        self.poll = 0
        self.until = None
        self.retries = None
        self.delay = 0
        self.timeout = 0
        self.notify = None

        # Connection/become-ish defaults used by _get_connection in real code, but we stub _get_connection
        self.connection = None
        self.become = False
        self.become_method = None
        self.no_log = False
        self.environment = None
        self.module_defaults = {}
        self._ansible_internal_redirect_list = []
        self.collections = None

    def squash(self):
        return None

    def copy(self, exclude_parent=True, exclude_tasks=True):
        return self

    def dump_attrs(self):
        return {}

    def post_validate(self, templar=None):
        return None

    def evaluate_conditional(self, templar, variables):
        return True

    def get_search_path(self):
        return []


class _PlayContext:
    def __init__(self, password=None, become_pass=None):
        self.password = password
        self.become_pass = become_pass
        self.remote_addr = None
        self.no_log = False
        self.verbosity = 0

    def set_task_and_variable_override(self, task=None, variables=None, templar=None):
        return self

    def post_validate(self, templar=None):
        return None

    def update_vars(self, variables):
        # Keep it simple: do nothing for this test
        return None

    def copy(self):
        return _PlayContext(password=self.password, become_pass=self.become_pass)


class _DummyTemplar:
    def __init__(self, available_variables):
        self.available_variables = available_variables


def test_delegation_does_not_combine_inventory_hostname_vars_into_delegated_host_cvars():
    """
    Regression test for delegation variable handling:

    When delegating, TaskExecutor should use ONLY the delegated host vars
    (ansible_delegated_vars[delegate_to]) as cvars, and must NOT combine them
    with the original host/inventory_hostname vars. Combining can leak
    inventory_hostname-specific credentials (e.g. ansible_password) onto the
    delegated host.
    """
    host = _Host(name="orig", address="1.2.3.4")
    task = _Task(delegate_to="delegated")
    play_context = _PlayContext(password="CLI_PASSWORD_SHOULD_BE_IN_TASK_KEYS_NOT_CVARS")
    te = TaskExecutor(
        host=host,
        task=task,
        job_vars={},
        play_context=play_context,
        new_stdin=None,
        loader=None,
        shared_loader_obj=None,
        final_q=None,
    )

    # Prepare variables where the original host has ansible_password set,
    # but the delegated host does not. We want to ensure cvars does NOT
    # include the original ansible_password when delegating.
    variables = {
        "inventory_hostname": "orig",
        "ansible_password": "ORIG_HOST_PASSWORD_SHOULD_NOT_LEAK",
        "ansible_delegated_vars": {
            "delegated": {
                "inventory_hostname": "delegated",
                # Intentionally no ansible_password in delegated vars
                "some_var": "x",
            }
        },
    }

    captured = {}

    # Stub out the heavy parts: we only need to drive up to the point where
    # cvars is computed and assigned to templar.available_variables.
    def _fake_get_connection(self, cvars, templar):
        return object()

    def _fake_set_connection_options(self, variables_for_conn, templar_for_conn):
        # Capture the exact variables passed to connection option resolution.
        captured["cvars"] = dict(variables_for_conn)
        # Stop execution before action handler is needed.
        raise RuntimeError("stop after capturing cvars")

    te._get_connection = _fake_get_connection.__get__(te, TaskExecutor)
    te._set_connection_options = _fake_set_connection_options.__get__(te, TaskExecutor)

    # Also stub Templar creation inside _execute by injecting a minimal object.
    # We'll do that by temporarily replacing the module's Templar symbol.
    import lib.ansible.executor.task_executor as te_mod

    orig_templar_cls = te_mod.Templar
    te_mod.Templar = lambda loader, shared_loader_obj, variables: _DummyTemplar(available_variables=variables)
    try:
        with pytest.raises(RuntimeError, match="stop after capturing cvars"):
            te._execute(variables=variables)
    finally:
        te_mod.Templar = orig_templar_cls

    assert "cvars" in captured, "Test did not capture cvars; the stubbed _set_connection_options was not reached"

    assert "ansible_password" not in captured["cvars"], (
        "Delegated execution must not combine original host vars into delegated host vars; "
        "ansible_password from inventory_hostname leaked into delegated host cvars"
    )