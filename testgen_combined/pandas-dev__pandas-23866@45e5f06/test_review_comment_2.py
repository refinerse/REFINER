import re


def test_setup_conda_environment_activates_env_before_removing_pandas():
    """
    The script must activate the newly created conda env before attempting to remove
    pandas from it. Without activation, `conda remove pandas` would run in the wrong
    environment (typically base/root).
    """
    path = "/workspace/ci/incremental/setup_conda_environment.sh"
    source = open(path, "r", encoding="utf-8").read()

    remove_idx = source.find("conda remove pandas -y --force || true")
    assert remove_idx != -1, "Expected the script to remove pandas via conda, but the command was not found."

    # Find the last "source activate pandas-dev" occurring before the pandas removal command.
    # This specifically checks the review request: activation can't be removed because the next
    # step removes pandas from the environment, so it needs to be active.
    activation_matches = list(re.finditer(r"^\s*source\s+activate\s+pandas-dev\s*$", source, flags=re.MULTILINE))
    activation_before = [m for m in activation_matches if m.start() < remove_idx]

    assert activation_before, (
        "Expected `source activate pandas-dev` to occur before `conda remove pandas ...`, "
        "so pandas is removed from the intended environment. No such activation was found before the removal."
    )