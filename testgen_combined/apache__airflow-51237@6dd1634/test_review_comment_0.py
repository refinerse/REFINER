import re


def test_is_test_only_changes_uses_local_git_diff_not_github_token_or_requests():
    source_path = "/workspace/dev/breeze/src/airflow_breeze/prepare_providers/provider_documentation.py"
    source = open(source_path).read()

    # Key behavior change: do not require GitHub token/requests; use local git diff on commit hash.
    assert "def _is_test_only_changes(commit_hash: str)" in source, (
        "_is_test_only_changes should accept a commit hash (local git data), not a PR number "
        "that requires GitHub API access."
    )

    assert '["git", "diff", "--name-only", f"{commit_hash}^", commit_hash]' in source, (
        "_is_test_only_changes should use a local `git diff --name-only <hash>^ <hash>` command "
        "to determine changed files without GitHub authentication."
    )

    # Ensure the old behavior is not present: querying GitHub API /pulls/{pr}/files via requests + token.
    assert "/pulls/" not in source, (
        "The implementation should not query GitHub API endpoints like /pulls/<pr>/files; "
        "it should rely on the local git repository."
    )
    assert "import requests" not in source, (
        "The implementation should not depend on the `requests` library for GitHub API calls."
    )
    assert "GITHUB_TOKEN" not in source, (
        "The interactive command should not require/use GITHUB_TOKEN for classifying test-only changes."
    )

    # Ensure update_release_notes uses commit hash (full_hash) rather than PR number.
    assert "_is_test_only_changes(change.full_hash)" in source, (
        "update_release_notes should call _is_test_only_changes with change.full_hash (commit hash), "
        "not with change.pr (PR number)."
    )

    # Additional sanity: function should still use the same provider tests path regex.
    assert re.search(r"re\.match\(r\"airflow/providers/\[\^/\]\+/tests/\"", source), (
        "_is_test_only_changes should continue to classify test-only changes based on "
        "airflow/providers/<provider>/tests/ path pattern."
    )