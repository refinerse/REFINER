import re


def test_no_pydantic_fallback_install_hack_in_branch_tip_dependency_cache():
    """
    The Dockerfile inlines scripts/docker/install_airflow_dependencies_from_branch_tip.sh.

    The review comment requests removing the hack:
        || pip install 'pydantic>=2' || true

    because it hides resolver issues and should instead be handled via
    EAGER_UPGRADE_ADDITIONAL_REQUIREMENTS when/if needed.

    This test ensures the hack is not present in the Dockerfile content.
    """
    source = open("/workspace/Dockerfile", "r", encoding="utf-8").read()

    assert "install_airflow_dependencies_from_branch_tip" in source, (
        "Sanity check failed: expected the inlined script "
        "install_airflow_dependencies_from_branch_tip to exist in /workspace/Dockerfile."
    )

    forbidden_patterns = [
        r"\|\|\s*pip\s+install\s+'pydantic>=2'\s*\|\|\s*true",
        r'\|\|\s*pip\s+install\s+"pydantic>=2"\s*\|\|\s*true',
        r"\|\|\s*pip\s+install\s+pydantic>=2\s*\|\|\s*true",
    ]
    for pat in forbidden_patterns:
        assert re.search(pat, source) is None, (
            "Dockerfile should not contain a fallback 'pip install pydantic>=2' chained with '|| ... || true' "
            "after the constrained install in install_airflow_dependencies_from_branch_tip. "
            "If eager-upgrade resolution needs help, it should be done via EAGER_UPGRADE_ADDITIONAL_REQUIREMENTS "
            "(e.g. adding 'pydantic>=2') rather than this hack."
        )