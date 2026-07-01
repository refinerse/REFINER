import pytest

import lib.ansible.modules.cloud.amazon.elb_classic_lb_facts as mod


def test_main_does_not_require_explicit_region():
    """
    Review intent: boto_conn (boto3_conn) now handles missing regions, so this module
    should not fail early with 'region must be specified' when region is absent.
    """

    # Call main() directly but ensure it never makes real AWS calls by supplying a
    # connection object that will satisfy subsequent code paths.
    class _DummyPaginator:
        def paginate(self, **kwargs):
            return self

        def build_full_result(self):
            return {"LoadBalancerDescriptions": []}

    class _DummyConnection:
        def get_paginator(self, name):
            assert name == "describe_load_balancers"
            return _DummyPaginator()

    # Provide minimal module implementation used by main().
    class _DummyModule:
        def __init__(self, *args, **kwargs):
            # main() reads module.params.get('names')
            self.params = {"names": []}

        def fail_json(self, **kwargs):
            raise RuntimeError(("fail_json", kwargs))

        def fail_json_aws(self, exc, msg=None, **kwargs):
            raise RuntimeError(("fail_json_aws", msg, repr(exc), kwargs))

        def exit_json(self, **kwargs):
            raise SystemExit(kwargs)

    # Monkeypatching via direct assignment (not unittest.mock) so the test runs
    # against both versions without external dependencies.
    old_module_cls = mod.AnsibleAWSModule
    old_get_info = mod.get_aws_connection_info
    old_boto3_conn = mod.boto3_conn
    old_list_elbs = mod.list_elbs

    try:
        mod.AnsibleAWSModule = _DummyModule
        # Simulate "no region returned" case.
        mod.get_aws_connection_info = lambda module, boto3=True: (None, None, {})
        mod.boto3_conn = lambda module, **kwargs: _DummyConnection()

        # Avoid calling get_tags / health / attributes by returning empty list.
        mod.list_elbs = lambda connection, names: []

        with pytest.raises(SystemExit) as e:
            mod.main()

        payload = e.value.args[0]
        assert "elbs" in payload, (
            "Module should succeed (exit_json) even when get_aws_connection_info returns "
            "no region; boto3_conn is expected to handle missing region."
        )
    except RuntimeError as e:
        marker = e.args[0]
        if isinstance(marker, tuple) and marker and marker[0] == "fail_json":
            kwargs = marker[1]
            assert kwargs.get("msg") != "region must be specified", (
                "Module should not fail early with 'region must be specified'; "
                "missing region should be handled by boto3_conn."
            )
        raise
    finally:
        mod.AnsibleAWSModule = old_module_cls
        mod.get_aws_connection_info = old_get_info
        mod.boto3_conn = old_boto3_conn
        mod.list_elbs = old_list_elbs