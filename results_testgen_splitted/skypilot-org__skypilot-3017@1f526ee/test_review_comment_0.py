import re


def test_mixtral_serve_yaml_does_not_remove_system_nccl_conf():
    source = open("/workspace/llm/mixtral/serve.yaml", "r", encoding="utf-8").read()

    # The review resolution moved the Azure-specific workaround elsewhere (azure-ray.yml.j2),
    # so the Mixtral serve.yaml should NOT mutate /etc/nccl.conf.
    forbidden_patterns = [
        r"sudo\s+mv\s+/etc/nccl\.conf\s+/etc/nccl\.conf\.bak",
        r"mv\s+/etc/nccl\.conf\s+/etc/nccl\.conf\.bak",
        r"/etc/nccl\.conf\.bak",
        r"Remove the default nccl\.conf",
    ]

    for pat in forbidden_patterns:
        assert re.search(pat, source) is None, (
            "Mixtral serve.yaml should not include an Azure-specific side-effect that "
            "moves/removes the system-wide /etc/nccl.conf. This workaround should live "
            "in Azure templates (e.g., azure-ray.yml.j2), not in llm/mixtral/serve.yaml. "
            f"Found forbidden pattern: {pat!r}"
        )