import pytest

import lib.ansible.modules.cloud.amazon.elb_classic_lb_facts as mod


def test_main_does_not_require_explicit_region_when_using_boto3_conn(monkeypatch):
    """
    Review intent: boto3_conn handles region resolution; module should no longer
    hard-fail with 'region must be specified' when region is not explicitly set.
    This test simulates missing region and asserts main() proceeds to exit_json.
    """

    class _ExitJson(Exception):
        def __init__(self, kwargs):
            super().__init__("exit_json called")
            self.kwargs = kwargs

    class _FailJson(Exception):
        def __init__(self, msg):
            super().__init__(msg)
            self.msg = msg

    class FakeModule:
        def __init__(self, *args, **kwargs):
            self.params = {"names": []}

        def exit_json(self, **kwargs):
            raise _ExitJson(kwargs)

        def fail_json(self, msg, **kwargs):
            raise _FailJson(msg)

        def fail_json_aws(self, e, msg, **kwargs):
            raise _FailJson(msg)

    # Avoid depending on real Ansible CLI/module invocation.
    monkeypatch.setattr(mod, "AnsibleAWSModule", FakeModule)

    # Simulate environment where get_aws_connection_info cannot determine a region.
    # Before fix: main() checks "if not region: fail_json('region must be specified')"
    # After fix: boto3_conn should be allowed to handle this (no explicit fail).
    monkeypatch.setattr(mod, "get_aws_connection_info", lambda module, boto3=False: (None, None, {}))

    # Prevent any real boto3/botocore usage; provide minimal fake connection.
    class FakeConnection:
        def get_paginator(self, name):
            class P:
                def paginate(self, **kwargs):
                    class R:
                        def build_full_result(self):
                            return {"LoadBalancerDescriptions": []}

                    return R()

            return P()

    monkeypatch.setattr(mod, "boto3_conn", lambda *a, **kw: FakeConnection())

    # If list_elbs is called, return deterministic empty list.
    monkeypatch.setattr(mod, "list_elbs", lambda connection, names: [])

    try:
        mod.main()
        pytest.fail("main() should have called exit_json (signaled by _ExitJson).")
    except _ExitJson as e:
        assert "elbs" in e.kwargs, (
            "Expected module to exit successfully with key 'elbs' (after change), "
            f"got keys: {sorted(e.kwargs.keys())}"
        )
    except _FailJson as e:
        assert e.msg != "region must be specified", (
            "Module should not hard-fail when region is not explicitly specified; "
            "boto3_conn is expected to handle region resolution."
        )
        pytest.fail(f"main() unexpectedly failed: {e.msg}")