import re


def test_is_local_substring_list_has_commas_and_separate_entries():
    source = open("/workspace/openhands/llm/llm.py", "r", encoding="utf-8").read()

    # Find the specific list literal used in _is_local()
    # We avoid AST parsing per instructions and use a simple regex over the source text.
    m = re.search(
        r"for\s+substring\s+in\s+\[(?P<items>[^\]]+)\]\s*:\s*\n\s*if\s+substring\s+in\s+self\.config\.base_url",
        source,
        flags=re.MULTILINE,
    )
    assert m, "Expected _is_local() to iterate over a list of substrings for base_url matching."

    items = m.group("items")

    # The bug was a missing comma between '127.0.0.1' and '0.0.0.0', which concatenates them into one string.
    assert "'127.0.0.1', '0.0.0.0'" in items, (
        "Expected _is_local() substring list to include separate entries "
        "'127.0.0.1' and '0.0.0.0' (i.e., a comma between them). "
        "Without the comma, Python concatenates adjacent string literals and local base_url detection breaks."
    )

    assert "'127.0.0.10.0.0.0'" not in items, (
        "Did not expect concatenated string literal '127.0.0.10.0.0.0' in _is_local(); "
        "this indicates the missing-comma bug is still present."
    )