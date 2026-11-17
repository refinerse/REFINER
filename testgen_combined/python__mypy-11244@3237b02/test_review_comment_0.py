import re


def test_typeddict_union_setitem_uses_dunder_setitem_call_present() -> None:
    source = open("/workspace/test-data/unit/check-typeddict.test", encoding="utf-8").read()

    # The review comment asked to also try directly calling foo.__setitem__("z", "a")
    # in the TypedDict union setitem test case. This should be present in the test data.
    assert 'foo.__setitem__("z", "a")' in source, (
        "Expected check-typeddict.test to include a direct call to "
        'foo.__setitem__("z", "a") in the TypedDict union setitem test case, '
        "so mypy exercises this code path and it does not crash."
    )

    # Ensure we didn't match some unrelated 'foo.__setitem__' mention elsewhere:
    # it should be in the specific case block added/edited.
    m = re.search(
        r"(?s)^\[case testTypedDictUnionSetItem\].*?\n(?=^\[case |\Z)",
        source,
        flags=re.MULTILINE,
    )
    assert m, "Could not find the [case testTypedDictUnionSetItem] block in check-typeddict.test"
    case_block = m.group(0)
    assert 'foo.__setitem__("z", "a")' in case_block, (
        'Found foo.__setitem__("z", "a") in the file, but not inside '
        "[case testTypedDictUnionSetItem]; it must be tested in that case."
    )