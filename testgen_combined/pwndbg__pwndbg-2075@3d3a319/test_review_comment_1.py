import re


def test_lint_workflow_mypy_reporter_is_check_not_review():
    source = open("/workspace/.github/workflows/lint.yml", "r", encoding="utf-8").read()

    # Locate the "Run mypy" step and capture its `reporter:` line.
    m = re.search(
        r"(?ms)^\s*-\s*name:\s*Run mypy\s*$.*?^\s*reporter:\s*([^\s#]+)\s*$",
        source,
    )
    assert m is not None, (
        "Expected the GitHub Actions workflow /workspace/.github/workflows/lint.yml to contain "
        "a step named 'Run mypy' with a 'reporter:' setting."
    )

    reporter_value = m.group(1).strip()
    assert reporter_value in {"github-pr-check", "github-check"}, (
        "Review comment requests using a GitHub status check reporter for mypy (e.g. "
        "`reporter: github-check` or `reporter: github-pr-check`) instead of PR review comments. "
        f"Found reporter={reporter_value!r} in the 'Run mypy' step."
    )

    assert reporter_value != "github-pr-review", (
        "The mypy step should not use `reporter: github-pr-review`; it should use a GitHub check "
        "reporter (`github-check` or `github-pr-check`) so annotations appear as status checks."
    )