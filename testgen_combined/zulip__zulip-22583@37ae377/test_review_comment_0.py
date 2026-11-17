import re

import pytest


def test_unread_mention_info_has_left_margin_to_prevent_overflow() -> None:
    source = open("/workspace/static/styles/app_components.css").read()

    # Locate the CSS rule added to address the overflow bug.
    # We then assert it includes a 2px left margin, as suggested in the review.
    m = re.search(
        r"\.unread_mention_info:not\(:empty\)\s*\{(?P<body>[^}]*)\}",
        source,
        flags=re.DOTALL,
    )
    assert m is not None, (
        "Expected a CSS rule for `.unread_mention_info:not(:empty)` to exist "
        "to address the overflow issue, but it was not found in "
        "/workspace/static/styles/app_components.css."
    )

    body = m.group("body")
    assert re.search(r"margin-left\s*:\s*2px\s*;", body) is not None, (
        "Expected `.unread_mention_info:not(:empty)` CSS rule to include "
        "`margin-left: 2px;` (to fix the overflow issue), but it was missing. "
        f"Rule body was:\n{body}"
    )