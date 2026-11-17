import re


def test_bookmark_ordering_uses_alphabetical_label_and_both_directions():
    source = open("/workspace/netbox/extras/choices.py").read()

    # The review requests changing "Name" ordering label to "Alphabetical" and
    # the final code adds both A-Z and Z-A variants.
    assert "BookmarkOrderingChoices" in source, "Expected BookmarkOrderingChoices to exist in choices.py"

    # Must not retain the old label
    assert (
        "('Name (A-Z)')" not in source
    ), "Bookmark ordering label should not be 'Name (A-Z)'; it should be labeled 'Alphabetical' for accuracy."

    # Must include the new alphabetical labels
    assert (
        "('Alphabetical (A-Z)')" in source
    ), "Expected bookmark ordering label 'Alphabetical (A-Z)' to be present."

    assert (
        "('Alphabetical (Z-A)')" in source
    ), "Expected bookmark ordering label 'Alphabetical (Z-A)' to be present."

    # Must define both constants (A-Z and Z-A)
    assert re.search(r"ORDERING_ALPHABETICAL_AZ\s*=\s*'name'", source), (
        "Expected constant ORDERING_ALPHABETICAL_AZ = 'name' to be defined for alphabetical A-Z ordering."
    )
    assert re.search(r"ORDERING_ALPHABETICAL_ZA\s*=\s*'-name'", source), (
        "Expected constant ORDERING_ALPHABETICAL_ZA = '-name' to be defined for alphabetical Z-A ordering."
    )