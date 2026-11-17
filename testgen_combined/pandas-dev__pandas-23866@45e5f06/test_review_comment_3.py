import re


def test_setup_conda_environment_does_not_hardcode_env_name_in_create():
    source = open("/workspace/ci/incremental/setup_conda_environment.sh", encoding="utf-8").read()

    # The review comment indicates that specifying "-n pandas-dev" during `conda env create`
    # is not needed. The updated script should therefore *not* include an explicit "-n pandas-dev"
    # on the `conda env create` line.
    assert (
        "conda env create" in source
    ), "Expected the setup script to run `conda env create`, but no such command was found."

    assert not re.search(
        r"^\s*(?:time\s+)?conda\s+env\s+create\b.*\s-n\s+pandas-dev\b",
        source,
        flags=re.MULTILINE,
    ), (
        "The conda environment creation should not hardcode the environment name via "
        "`conda env create ... -n pandas-dev`. The script should rely on the environment file "
        "or activate the desired env afterwards."
    )