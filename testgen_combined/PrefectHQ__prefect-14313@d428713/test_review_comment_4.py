import re


def test_deploy_docs_frontmatter_removes_mkdocs_tags_and_search_boost_only():
    """
    Review comment: "tags and search->boost are left over metadata from mkdocs that we should remove."

    The corrected doc (after) removes:
      - the `tags:` frontmatter key
      - the `search:` frontmatter *boost* setting (i.e., `search:\n  boost: 2`)
    but still keeps an empty `search:` key.

    This test must:
      - FAIL on before: tags exist and search.boost exists
      - PASS on after: tags removed and search.boost removed
    """
    path = "/workspace/docs/3.0rc/deploy/index.mdx"
    source = open(path, "r", encoding="utf-8").read()

    # Extract frontmatter between first two '---' lines
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", source, flags=re.DOTALL)
    assert m, f"Expected MDX file to start with frontmatter delimited by '---' in {path}"
    frontmatter = m.group(1)

    assert re.search(r"(?m)^\s*tags\s*:", frontmatter) is None, (
        "Frontmatter still contains a 'tags:' key. The review comment requests removing leftover "
        "MkDocs metadata (tags) from docs/3.0rc/deploy/index.mdx."
    )

    assert re.search(r"(?m)^\s*boost\s*:", frontmatter) is None, (
        "Frontmatter still contains a 'boost:' key (under search). The review comment requests "
        "removing leftover MkDocs metadata (search->boost) from docs/3.0rc/deploy/index.mdx."
    )