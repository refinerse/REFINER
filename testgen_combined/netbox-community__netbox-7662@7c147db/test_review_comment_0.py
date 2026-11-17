import re


def test_declared_filter_lookup_validation_is_present():
    """
    Ensure BaseFilterSet validates lookup expressions for explicitly declared filters
    by calling resolve_field(field, lookup_expr) before instantiating the new filter.

    This sanity-check should be present to raise/catch FieldLookupError for invalid lookups.
    """
    source = open("/workspace/netbox/netbox/filtersets.py", "r", encoding="utf-8").read()

    # We specifically expect the restored sanity check inside the branch that handles
    # explicitly declared filters (existing_filter_name in cls.declared_filters).
    pattern = re.compile(
        r"if\s+existing_filter_name\s+in\s+cls\.declared_filters\s*:\s*"
        r"(?:#.*\n|\s*\n)*"
        r".*?\n"
        r"\s*resolve_field\s*\(\s*field\s*,\s*lookup_expr\s*\)",
        re.DOTALL,
    )

    assert pattern.search(source), (
        "Expected BaseFilterSet to validate lookup expressions for explicitly declared filters via "
        "`resolve_field(field, lookup_expr)` (sanity-check for invalid lookups). This call was missing."
    )