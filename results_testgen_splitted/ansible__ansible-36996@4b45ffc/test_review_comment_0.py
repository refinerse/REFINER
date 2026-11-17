import tempfile

import pytest

import lib.ansible.modules.cloud.misc.terraform as tf


class _ModuleStub:
    """
    Stub for the global `module` object used throughout terraform.py.
    It simulates a failing `terraform init` to make init_plugins observable.
    """

    def __init__(self, project_path, force_init):
        self.params = {
            "project_path": project_path,
            "binary_path": "/bin/true",
            "state": "planned",
            "variables": {},
            "variables_file": None,
            # In planned state, plan_file is ignored; keep it unset/None.
            "plan_file": None,
            "state_file": None,
            "targets": [],
            "lock": True,
            "lock_timeout": None,
            "force_init": force_init,
        }
        self.check_mode = True
        self.init_calls = 0

    def get_bin_path(self, name):
        return "/bin/true"

    def run_command(self, command, cwd=None):
        # Fail init, succeed everything else.
        if isinstance(command, (list, tuple)) and len(command) >= 2 and command[1] == "init":
            self.init_calls += 1
            return 1, "", "init failed"
        # validate/plan/output succeed
        return 0, "{}", ""

    def fail_json(self, **kwargs):
        raise RuntimeError(kwargs.get("msg", "fail_json called"))

    def warn(self, msg):
        pass

    def exit_json(self, **kwargs):
        raise SystemExit(kwargs)


def test_init_only_runs_when_force_init_true(monkeypatch):
    """
    Ensure init_plugins() is conditional:
    - when force_init=False: init should not run; module should complete successfully
    - when force_init=True: init should run; our stub makes it fail with init error
    """

    created = {}

    def _fake_ansible_module_ctor(*args, **kwargs):
        return created["module"]

    monkeypatch.setattr(tf, "AnsibleModule", _fake_ansible_module_ctor)

    with tempfile.TemporaryDirectory() as project_path:
        # Case 1: force_init=False -> init should NOT run and should exit_json successfully.
        created["module"] = _ModuleStub(project_path=project_path, force_init=False)

        with pytest.raises(SystemExit) as excinfo:
            tf.main()

        payload = excinfo.value.args[0]
        assert isinstance(payload, dict) and payload.get("state") == "planned", (
            "When force_init=False, the module should complete and call exit_json; "
            "it should not fail during terraform init."
        )
        assert created["module"].init_calls == 0, (
            "Expected terraform init not to be invoked when force_init is False, "
            f"but it was called {created['module'].init_calls} time(s)."
        )

        # Case 2: force_init=True -> init should run and fail early due to our stub.
        created["module"] = _ModuleStub(project_path=project_path, force_init=True)

        with pytest.raises(RuntimeError) as excinfo2:
            tf.main()

        assert "Failed to initialize Terraform modules" in str(excinfo2.value), (
            "When force_init=True, expected init_plugins() to run and fail early."
        )
        assert created["module"].init_calls == 1, (
            "Expected terraform init to be invoked exactly once when force_init=True, "
            f"but it was called {created['module'].init_calls} time(s)."
        )