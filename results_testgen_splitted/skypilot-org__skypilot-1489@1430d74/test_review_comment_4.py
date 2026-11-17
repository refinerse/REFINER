import glob
import re


def test_pass_role_policy_inline_name_is_clear_and_not_iam_self_read_write():
    # The repository layout may differ between "before" and "after".
    # Look for the AWS provider config file(s) robustly.
    candidates = sorted(glob.glob("/workspace/**/config_v2.py", recursive=True))

    # In the corrected ("after") version, the file under review may have been
    # moved/removed/renamed. In that case, we should still validate the behavior
    # change by checking the repository source for the new/old policy names.
    if candidates:
        sources = []
        for p in candidates:
            try:
                sources.append(open(p, "r", encoding="utf-8").read())
            except OSError:
                continue
        full_source = "\n\n".join(sources)
    else:
        # Fallback: scan all Python files under the AWS provider directory if present,
        # otherwise scan all Python files in the repo.
        aws_py = sorted(
            glob.glob("/workspace/sky/skylet/providers/aws/**/*.py", recursive=True)
        )
        if not aws_py:
            aws_py = sorted(glob.glob("/workspace/**/*.py", recursive=True))
        assert aws_py, "Expected to find Python source files under /workspace/ to scan."

        sources = []
        for p in aws_py:
            try:
                sources.append(open(p, "r", encoding="utf-8").read())
            except OSError:
                continue
        full_source = "\n\n".join(sources)

    # After the change, the confusing name should be gone and replaced by the clearer one.
    assert "SkypilotPassRolePolicy" in full_source, (
        "Expected the inline IAM policy to be named 'SkypilotPassRolePolicy' "
        "(clearer than 'IAMSelfReadWritePolicy') somewhere in the AWS provider code."
    )
    assert "IAMSelfReadWritePolicy" not in full_source, (
        "Did not expect to find the old confusing inline policy name "
        "'IAMSelfReadWritePolicy' after the rename."
    )

    # Ensure the new name is actually used in a role.Policy(...).put(...) call.
    assert re.search(
        r'\.Policy\(\s*["\']SkypilotPassRolePolicy["\']\s*\)\.put\(',
        full_source,
    ), (
        "Expected code to attach/put the inline policy using "
        ".Policy('SkypilotPassRolePolicy').put(...)."
    )