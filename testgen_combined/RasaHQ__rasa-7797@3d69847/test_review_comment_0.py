import re


def test_wait_for_docs_tests_job_has_no_if_condition_anymore():
    """
    The review comment indicates the `if:` condition on the `wait_for_docs_tests` job
    was a copy/paste error and should be removed.

    This test asserts that within the `wait_for_docs_tests:` job definition there is
    no job-level `if:` key.
    """
    workflow_path = "/workspace/.github/workflows/continous-integration.yml"
    source = open(workflow_path, encoding="utf-8").read()

    # Extract the block for the `wait_for_docs_tests:` job until the next job at 2-space indent
    m = re.search(
        r"(?ms)^[ ]{2}wait_for_docs_tests:\n(.*?)(?=^[ ]{2}[A-Za-z0-9_.-]+:\n|\Z)",
        source,
    )
    assert m, "Expected to find a `wait_for_docs_tests:` job in the workflow file."

    job_block = m.group(0)

    # Job-level `if:` would appear at 4-space indent inside the job block.
    assert (
        re.search(r"(?m)^[ ]{4}if:\s*", job_block) is None
    ), (
        "The `wait_for_docs_tests` job should not define a job-level `if:` condition. "
        "The review comment indicates this `if:` was a copy/paste error and must be removed."
    )