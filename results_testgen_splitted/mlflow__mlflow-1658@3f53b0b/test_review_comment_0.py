import re


def test_local_artifact_repo_list_artifacts_does_not_append_list_dir():
    """
    The review change removes a hack where list_artifacts() appended the directory being listed
    (`list_dir`) to the results:
        artifact_files = list_all(list_dir, full_path=True) + [list_dir]

    This test enforces that the implementation no longer appends `[list_dir]` to `artifact_files`.
    """
    source = open("/workspace/mlflow/store/local_artifact_repo.py", "r", encoding="utf-8").read()

    # This is the problematic pattern from the "before" code: appending [list_dir]
    bad_pattern = re.compile(
        r"artifact_files\s*=\s*list_all\(\s*list_dir\s*,\s*full_path\s*=\s*True\s*\)\s*\+\s*\[\s*list_dir\s*\]"
    )

    assert not bad_pattern.search(source), (
        "LocalArtifactRepository.list_artifacts() must not append the listed directory itself "
        "to artifact_files (i.e. no `+ [list_dir]`). This hack caused incorrect list results; "
        "the code should just use `artifact_files = list_all(list_dir, full_path=True)`."
    )