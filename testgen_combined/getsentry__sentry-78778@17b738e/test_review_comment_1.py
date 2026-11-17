import re


def test_devtoolbar_middleware_uses_guard_clause_and_not_nested_if():
    source = open("/workspace/src/sentry/middleware/devtoolbar.py").read()

    # Style expectation from review: replace nested conditional with guard clauses / early return.
    # In the "before" code, the file contains a nested conditional inside try:
    #     try:
    #         if request.headers.get("queryReferrer") == "devtoolbar":
    #
    # In the "after" code, the conditional lives in __call__ and uses a combined guard:
    #     if request.headers.get("queryReferrer") == "devtoolbar" and options.get(...):
    #
    # We assert the nested-if pattern is gone, and that a guard-style combined conditional exists.
    nested_if_pattern = re.compile(
        r"try:\s*\n\s*if\s+request\.headers\.get\(\s*[\"']queryReferrer[\"']\s*\)\s*==\s*[\"']devtoolbar[\"']\s*:",
        re.MULTILINE,
    )
    assert not nested_if_pattern.search(source), (
        "Expected the devtoolbar analytics logic to avoid a nested `if` inside a `try:` block "
        "(replace nested conditional with guard clauses / early return). Found the old pattern:\n"
        "    try:\n"
        "        if request.headers.get('queryReferrer') == 'devtoolbar':"
    )

    guard_if_pattern = re.compile(
        r"if\s+request\.headers\.get\(\s*[\"']queryReferrer[\"']\s*\)\s*==\s*[\"']devtoolbar[\"']\s*and\s+options\.get\(",
        re.MULTILINE,
    )
    assert guard_if_pattern.search(source), (
        "Expected a guard-style combined conditional for devtoolbar analytics, e.g.\n"
        "    if request.headers.get('queryReferrer') == 'devtoolbar' and options.get(...):\n"
        "This indicates the code was refactored away from the nested conditional."
    )