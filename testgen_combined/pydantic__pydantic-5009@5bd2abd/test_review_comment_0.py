import re


def test_collect_fields_typevars_map_not_double_applied_regression():
    source = open("/workspace/pydantic/_internal/_fields.py", "r", encoding="utf-8").read()

    # The bug: inside the for-loop over type_hints, the "before" code re-reads
    # __pydantic_generic_typevars_map__ and applies replace_types there, and then applies
    # the (same) map again after the loop, effectively double-applying substitutions.
    #
    # The fix: hoist pydantic_generic_typevars_map = getattr(...) out of the loop and use it
    # after the loop: `typevars_map = pydantic_generic_typevars_map or typevars_map`.
    #
    # We source-inspect due to import failures in the provided environment.
    assert (
        "typevars_map = pydantic_generic_typevars_map or typevars_map" in source
    ), "Regression check: collect_fields should prefer the already-applied pydantic_generic_typevars_map " \
       "when applying final substitutions (avoids double-apply). Expected to find: " \
       "'typevars_map = pydantic_generic_typevars_map or typevars_map'."

    # Ensure the old, buggy pattern (re-getting the map inside the loop) is not present.
    # This is kept relatively strict to avoid false positives.
    buggy_loop_pattern = re.compile(
        r"for\s+ann_name,\s*ann_type\s+in\s+type_hints\.items\(\):.*?"
        r"pydantic_generic_typevars_map\s*=\s*getattr\(\s*cls\s*,\s*'__pydantic_generic_typevars_map__'\s*,\s*None\s*\)",
        re.DOTALL,
    )
    assert (
        buggy_loop_pattern.search(source) is None
    ), "Regression check: collect_fields should not fetch __pydantic_generic_typevars_map__ inside the " \
       "type-hints loop (that enables a double-apply of typevar substitution)."