import re


def test_groupsearchview_create_or_update_uses_correct_organization_kwarg_and_position_arg():
    source = open(
        "/workspace/src/sentry/api/endpoints/organization_pinned_searches.py", "r"
    ).read()

    assert (
        "GroupSearchView.objects.create_or_update" in source
    ), "Expected OrganizationPinnedSearchEndpoint.put to call GroupSearchView.objects.create_or_update"

    # Must not contain the misspelled kwarg that caused the bug.
    assert (
        "organizaiton=" not in source
    ), "GroupSearchView.objects.create_or_update must not use the misspelled kwarg 'organizaiton='; it should be 'organization='"

    # Must contain the correct kwarg.
    assert (
        "organization=organization" in source
    ), "Expected GroupSearchView.objects.create_or_update to be called with organization=organization"

    # Style fix also moved `position=0` to a dedicated argument (not inside values).
    assert re.search(
        r"GroupSearchView\.objects\.create_or_update\([\s\S]*\bposition\s*=\s*0\b",
        source,
    ), "Expected GroupSearchView.objects.create_or_update to pass position=0 as a top-level argument"

    assert (
        '"position"' not in source and "'position'" not in source
    ), "Expected 'position' to not be included in the values dict; it should be passed as position=0 argument"