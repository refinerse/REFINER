# Pytest cannot be imported in this execution environment due to dependency issues.
# This file is still a valid "pytest-style" test module because it only uses plain
# `assert` statements and reads the repository source directly.

def test_customerfilter_ids_help_text_has_period_before_added_in_marker():
    source = open("/workspace/saleor/graphql/account/filters.py", "r", encoding="utf-8").read()

    expected = 'help_text=f"Filter by ids. {ADDED_IN_38}"'
    before = 'help_text=f"Filter by ids {ADDED_IN_38}"'

    assert expected in source, (
        "Style requirement: CustomerFilter.ids help_text should include a period after "
        "'ids' before the ADDED_IN_38 marker. Expected to find:\n"
        f"  {expected}"
    )
    assert before not in source, (
        "Found the pre-review help_text format (missing period after 'ids'). "
        "The help_text should be updated to include the period:\n"
        f"  Unexpected: {before}\n"
        f"  Expected:   {expected}"
    )