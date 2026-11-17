import re


def test_modify_unmatched_object_uses_get_for_interpolated_shapes_guard():
    """
    Functional intent: when updating cached interpolated shapes, the code should
    use a safe truthy check via dict.get to avoid redundant key checks and ensure
    consistent behavior when the key is missing/empty.
    """
    source = open("/workspace/cvat/apps/engine/data_manager.py", "r", encoding="utf-8").read()

    # Ensure we're checking the exact guard in the reviewed hunk.
    expected_guard = "if obj.get(\"interpolated_shapes\"):"
    forbidden_guard = "if \"interpolated_shapes\" in obj and obj[\"interpolated_shapes\"]:"

    assert expected_guard in source, (
        "Expected TrackManager._modify_unmached_object to guard interpolated shape cache updates "
        "with `if obj.get(\"interpolated_shapes\"):` (reviewed change), but it was not found."
    )

    assert forbidden_guard not in source, (
        "Did not expect the old guard `if \"interpolated_shapes\" in obj and obj[\"interpolated_shapes\"]:` "
        "to remain after the review change."
    )

    # Extra robustness: ensure the expected guard appears in the correct context (near the cache update comment).
    pattern = re.compile(
        r"Need to update cached interpolated shapes[\s\S]{0,300}if obj\.get\(\"interpolated_shapes\"\):"
    )
    assert pattern.search(source), (
        "Found `if obj.get(\"interpolated_shapes\"):` but not in the expected context near the "
        "'Need to update cached interpolated shapes' section."
    )