import re


def test_groupsearchview_create_or_update_includes_position_in_select_criteria():
    source = open(
        "/workspace/src/sentry/api/endpoints/organization_pinned_searches.py", "r", encoding="utf-8"
    ).read()

    # The review comment requests that `position` be part of the select criteria
    # for GroupSearchView.objects.create_or_update(...), i.e. passed as a top-level
    # kwarg (not inside `values={...}`).
    #
    # This should look like:
    #   GroupSearchView.objects.create_or_update(
    #       organization=organization,
    #       user_id=request.user.id,
    #       position=0,
    #       values={...}
    #   )
    #
    # The "before" code incorrectly put "position" inside values and also misspelled
    # organization as "organizaiton".
    m = re.search(
        r"GroupSearchView\.objects\.create_or_update\(\s*(?P<args>.*?)\)\s*",
        source,
        flags=re.DOTALL,
    )
    assert m, "Expected a GroupSearchView.objects.create_or_update(...) call in the endpoint."

    args = m.group("args")

    assert re.search(r"^\s*position\s*=\s*0\s*,", args, flags=re.MULTILINE), (
        "Expected GroupSearchView.objects.create_or_update(...) to include `position=0` "
        "as a top-level select criterion (unique is org, user, position)."
    )

    assert not re.search(r'values\s*=\s*\{[^}]*"position"\s*:', args, flags=re.DOTALL), (
        "Did not expect `position` to be inside the `values={...}` dict; it should be part of "
        "the select criteria passed directly to create_or_update(...)."
    )