import re


def test_type_alias_runtime_expression_todo_comment_added():
    source_path = "/workspace/test-data/unit/check-generics.test"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    required_todo = "# TODO: fix https://github.com/python/mypy/issues/7084."
    assert required_todo in source, (
        f"Expected the TODO comment to be present in {source_path!r} to document the known issue:\n"
        f"{required_todo!r}\n"
        "This should be added directly above the problematic 'ff = SameNode[T](1, 1)' line."
    )

    # The file is a mypy .test file; whitespace/newlines around the TODO may vary.
    # Check that within the specific case, the TODO appears after the SameNode alias
    # and before the ff assignment.
    case_header = "[case testGenericTypeAliasesRuntimeExpressionsInstance]"
    start = source.find(case_header)
    assert start != -1, f"Expected to find test case header {case_header!r} in {source_path!r}"

    # Take the slice for this case only (until the next [case ...] or EOF).
    next_case = source.find("\n[case ", start + 1)
    case_block = source[start:] if next_case == -1 else source[start:next_case]

    pattern = re.compile(
        r"SameNode\s*=\s*Node\[T,\s*T\][\s\S]*?"
        r"#\s*TODO:\s*fix\s+https://github\.com/python/mypy/issues/7084\.[\s\S]*?"
        r"ff\s*=\s*SameNode\[T\]\(1,\s*1\)",
        re.MULTILINE,
    )
    assert pattern.search(case_block), (
        "Expected, within [case testGenericTypeAliasesRuntimeExpressionsInstance], the TODO comment "
        "to appear between the 'SameNode = Node[T, T]' alias definition and the 'ff = SameNode[T](1, 1)' line."
    )