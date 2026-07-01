import re


def test_changelog_fragment_quotes_issue_url_and_avoids_yaml_comment_truncation():
    path = "/workspace/changelogs/fragments/56567-Fix-win_iis_website-id assignment-for-first-new-site.yml"
    source = open(path, "r", encoding="utf-8").read()

    # Ensure the bullet item is a single fully-quoted YAML string and includes a full GitHub URL.
    # This prevents `#47057` from being treated as a YAML comment and truncating the entry.
    assert re.search(r'^\s*-\s*".*https://github\.com/ansible/ansible/issues/47057.*"\s*$',
                     source, flags=re.MULTILINE), (
        "Changelog fragment entry must be a fully quoted YAML string containing the full issue URL "
        "(https://github.com/ansible/ansible/issues/47057) to avoid `#...` being parsed as a YAML comment."
    )