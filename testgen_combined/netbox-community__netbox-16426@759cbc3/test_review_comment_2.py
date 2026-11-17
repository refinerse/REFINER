import re


def test_bookmark_ordering_includes_reverse_alphabetical_option():
    source = open("/workspace/netbox/extras/choices.py", encoding="utf-8").read()

    # Extract the BookmarkOrderingChoices class block (up to next top-level class or EOF)
    m = re.search(
        r"(?ms)^\s*class\s+BookmarkOrderingChoices\b.*?:\s*(.*?)(?=^\s*class\s|\Z)",
        source,
    )
    assert m, "Expected to find class BookmarkOrderingChoices in /workspace/netbox/extras/choices.py"
    block = m.group(0)

    # Verify the reverse alphabetical constant exists and has the correct ordering value.
    assert re.search(
        r"(?m)^\s*ORDERING_ALPHABETICAL_ZA\s*=\s*['\"]-name['\"]\s*$",
        block,
    ), (
        "BookmarkOrderingChoices should define a reverse-alphabetical ordering option "
        "as ORDERING_ALPHABETICAL_ZA = '-name'."
    )

    # Verify the option is exposed via CHOICES with the expected label.
    assert re.search(
        r"(?m)^\s*\(\s*ORDERING_ALPHABETICAL_ZA\s*,\s*_\(\s*['\"]Alphabetical\s*\(Z-A\)['\"]\s*\)\s*\)\s*,\s*$",
        block,
    ), (
        "BookmarkOrderingChoices.CHOICES should include the reverse-alphabetical option tuple: "
        "(ORDERING_ALPHABETICAL_ZA, _('Alphabetical (Z-A)'))."
    )