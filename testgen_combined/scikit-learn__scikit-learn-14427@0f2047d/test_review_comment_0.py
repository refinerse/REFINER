import re


def test_assert_run_python_script_does_not_use_shell_true_and_sets_pythonpath():
    """
    The reviewed change removes 'shell=True' usage and instead ensures that
    PYTHONPATH is updated to include the sklearn repo root (cwd).

    This test is intentionally source-level to directly and robustly detect the
    specific change in the diff hunk.
    """
    source = open("/workspace/sklearn/utils/testing.py", "r", encoding="utf-8").read()

    # Strong assertion: the old problematic keyword argument must not be present.
    assert "'shell': True" not in source, (
        "assert_run_python_script should not use shell=True in subprocess kwargs; "
        "shell=True was present in sklearn/utils/testing.py"
    )

    # Strong assertion: the new behavior must be implemented: PYTHONPATH is set/updated.
    assert re.search(r'env\["PYTHONPATH"\]\s*=', source), (
        "assert_run_python_script should update env['PYTHONPATH'] to include the repo cwd, "
        "but no assignment to env['PYTHONPATH'] was found in sklearn/utils/testing.py"
    )