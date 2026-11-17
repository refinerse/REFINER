import re


def test_executor_args_docs_list_prefer_platform():
    """
    The merged ('after') version of the docs includes a `prefer_platform` row.
    This test asserts that row exists.

    NOTE: This is intentionally written to FAIL on the earlier ('before') version
    where the row is missing, and PASS on the later ('after') version.
    """
    source = open("/workspace/docs/concepts/flow/executor-args.md", "r", encoding="utf-8").read()

    pattern = r"^\|\s*`prefer_platform`\s*\|"
    assert re.search(pattern, source, flags=re.MULTILINE), (
        "Expected docs/concepts/flow/executor-args.md to include a markdown table row for "
        "`prefer_platform`, but it was not found."
    )