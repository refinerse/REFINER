# This file is intended to be executed by pytest, but the environment may have a broken
# pytest dependency stack. The test itself uses only plain asserts and stdlib.

import re


def test_review_requested_typed_ignore_and_justification_comment_present() -> None:
    source = open("/workspace/tests/core/daemon/test_daemon.py", "r", encoding="utf-8").read()

    # The pre-review code contained a bare ignore:
    #   return await WebSocketServer.is_running(self, request)  # type: ignore
    #
    # The review requested:
    #  - full ignore form: `# type: ignore[<code>]`
    #  - plus a comment on the previous line with a link/PR/justification.
    #
    # We enforce these by requiring:
    #  1) no bare `# type: ignore` anywhere, and
    #  2) if an ignore exists, it must be the bracketed form and preceded by a justification comment line.
    #
    # (The "after" code removes the ignore by using `cast(...)`, which also satisfies this.)

    # 1) No bare ignores anywhere.
    bare = re.search(r"#\s*type:\s*ignore(?!\s*\[)", source)
    assert bare is None, (
        "Found bare '# type: ignore' without an explicit error code. "
        "Use '# type: ignore[<error-code>]' and add a justification comment on the preceding line."
    )

    # 2) If bracketed ignores exist, require a justification comment immediately above.
    #    (Allows "after" to have zero ignores.)
    lines = source.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"#\s*type:\s*ignore\[[^\]]+\]", line):
            prev = lines[i - 1].strip() if i > 0 else ""
            assert prev.startswith("#") and (
                "http://" in prev
                or "https://" in prev
                or "PR" in prev
                or "TODO" in prev
                or "issue" in prev.lower()
                or "bug" in prev.lower()
                or "justification" in prev.lower()
            ), (
                "Found '# type: ignore[...'] but missing an adjacent justification comment on the previous line "
                "(expected link to bug/PR or long-term justification)."
            )