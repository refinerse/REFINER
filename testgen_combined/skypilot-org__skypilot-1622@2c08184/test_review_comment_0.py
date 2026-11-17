import pytest


def test_review_fix_applied_cpus_variants_in_instance_type_matches_cpus():
    # Functional execution of the optimizer dryrun path can trigger real cloud
    # catalog fetching (AWS regions) and fail in CI due to missing credentials.
    # The review comment change is strictly about which literals are used in
    # the test case: adding cpus='8' and cpus=8.0 variants. We validate that
    # observable change by inspecting the repository test source itself.
    source = open("/workspace/tests/test_optimizer_dryruns.py", "r").read()

    # The "after" version must include these variants in test_instance_type_matches_cpus.
    assert "def test_instance_type_matches_cpus" in source, (
        "Expected tests/test_optimizer_dryruns.py to define "
        "test_instance_type_matches_cpus()."
    )

    assert "cpus='8')" in source or 'cpus="8")' in source, (
        "Expected test_instance_type_matches_cpus() to include the variant "
        "cpus='8' for the Azure instance type, per the review comment."
    )
    assert "cpus=8.0)" in source, (
        "Expected test_instance_type_matches_cpus() to include the variant "
        "cpus=8.0 for the last resource, per the review comment."
    )

    # And it should no longer use the old int literal for Azure.
    assert "instance_type='Standard_E8s_v5',\n                           cpus=8)" not in source, (
        "Expected Azure case in test_instance_type_matches_cpus() to be updated "
        "from cpus=8 to cpus='8'."
    )