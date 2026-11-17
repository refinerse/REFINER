import re


def test_convert_skip_block_contains_todo_marker_comment():
    source_path = "/workspace/tests/nlu/test_train.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    # Find the specific `if "convert" in cls.name.lower():` block and assert it contains
    # the `# TODO` marker comment. This marker was missing in the "before" version and
    # restored in the "after" version.
    block_pattern = re.compile(
        r'for\s+cls\s+in\s+registry\.component_classes:\s*'
        r'\n\s*if\s+"convert"\s+in\s+cls\.name\.lower\(\):'
        r'(?P<body>(?:\n[ \t]+.*)*)',
        re.MULTILINE,
    )

    match = block_pattern.search(source)
    assert match is not None, (
        "Could not locate the `for cls in registry.component_classes` loop with the "
        '`if "convert" in cls.name.lower():` guard in /workspace/tests/nlu/test_train.py.'
    )

    body = match.group("body")
    assert re.search(r"\n[ \t]*#\s*TODO\b", body) is not None, (
        "Expected a `# TODO` comment inside the "
        '`if "convert" in cls.name.lower():` skip block. '
        "This should be present after the fix and absent before it."
    )