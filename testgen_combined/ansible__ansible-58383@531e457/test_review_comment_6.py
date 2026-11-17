import lib.ansible.modules.windows.win_domain_user as win_domain_user


def _extract_update_password_block(documentation: str) -> str:
    """
    Extract the 'update_password:' option block from the DOCUMENTATION YAML-ish text.

    We slice from the '  update_password:' line up to (but not including) the next
    option key at the same indent level, which is identified as '\n  <something>:\n'.
    """
    start_marker = "\n  update_password:\n"
    start = documentation.find(start_marker)
    assert start != -1, "Could not find 'update_password' option in DOCUMENTATION."
    start += 1  # drop the leading newline for readability

    rest = documentation[start:]

    # Find the next "two space indent option key" line after the update_password line.
    search_from = rest.find("\n", len("  update_password:"))
    assert search_from != -1, "Malformed DOCUMENTATION: could not find newline after 'update_password:' line."

    import re

    m = re.search(r"\n  [A-Za-z0-9_]+:\n", rest[search_from:])
    if not m:
        return rest
    return rest[: search_from + m.start() + 1]


def test_update_password_always_docstring_says_always_updates_password():
    """
    The review comment requests the docs to say:
      - C(always) will always update passwords.
    """
    doc = win_domain_user.DOCUMENTATION
    assert isinstance(doc, str) and doc.strip(), "Expected win_domain_user.DOCUMENTATION to be a non-empty string."

    block = _extract_update_password_block(doc)

    assert "C(always) will always update passwords." in block, (
        "Expected update_password docs to include the line "
        "'C(always) will always update passwords.' within the update_password option block."
    )