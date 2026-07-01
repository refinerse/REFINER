import re


def test_conda_env_create_does_not_override_name_with_n_flag():
    """
    The environment name is already defined in the YAML; the script should not
    pass `-n pandas-dev` to `conda env create`.
    """
    source = open("/workspace/ci/incremental/setup_conda_environment.cmd", encoding="utf-8").read()

    # Look for `conda env create ... -n pandas-dev ...` in any order on that line.
    pattern = re.compile(r"(?im)^\s*conda\s+env\s+create\b.*\s-n\s+pandas-dev\b")
    assert not pattern.search(source), (
        "setup_conda_environment.cmd should not pass `-n pandas-dev` to "
        "`conda env create` because the env name is defined in the YAML file."
    )