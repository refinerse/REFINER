import re


def test_linux_ci_does_not_activate_env_before_creation():
    """
    The review comment notes that the conda env is created in setup_conda_environment.sh,
    so linux.yml must NOT try to activate it before that step runs.

    This test fails on the "before" version because it contains
    'source activate pandas-dev' before 'ci/incremental/setup_conda_environment.sh',
    and passes on the "after" version where that premature activation is removed.
    """
    source = open("/workspace/ci/azure/linux.yml", encoding="utf-8").read()

    setup_token = "ci/incremental/setup_conda_environment.sh"
    assert setup_token in source, "Expected linux.yml to call setup_conda_environment.sh"

    # Find the first occurrence of the setup script call; ensure no activation occurs before it.
    setup_pos = source.find(setup_token)
    pre_setup = source[:setup_pos]

    assert "source activate pandas-dev" not in pre_setup, (
        "linux.yml activates 'pandas-dev' before calling setup_conda_environment.sh; "
        "this is incorrect because the env isn't created yet. Remove the activation "
        "from the 'Before Install' step (keep it only in later steps if needed)."
    )

    # Sanity check: activation is still allowed later (build/test/etc). Not required, but helps
    # ensure the test is checking the intended change rather than total removal.
    post_setup = source[setup_pos:]
    assert re.search(r"\bsource activate pandas-dev\b", post_setup), (
        "Expected 'source activate pandas-dev' to still be present after the environment setup, "
        "e.g., in Build/Test steps."
    )