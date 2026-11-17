import re

import pytest


def test_get_idranges_error_message_explains_original_numbers_of_id_ranges():
    """
    The review comment asked to clarify "original one" in the assertion error.
    Verify the assertion message was updated to mention "original numbers of ID ranges".
    """
    source = open("/workspace/tools/distpartitioning/utils.py", "r", encoding="utf-8").read()

    # Ensure we're checking the actual assertion message in get_idranges.
    assert "assert" in source and "num_chunks" in source and "orig_num_chunks" in source, (
        "Sanity check failed: expected get_idranges to contain an assertion about chunk counts."
    )

    expected_message_fragment = "original numbers of ID ranges"
    assert expected_message_fragment in source, (
        "Expected get_idranges assertion error message to be user-facing and explicit. "
        f"It should mention '{expected_message_fragment}' (clarifying what 'original' refers to)."
    )

    # Ensure the old unclear phrasing is not present (would confuse users).
    old_message_fragment = "original one"
    assert old_message_fragment not in source, (
        "Found old unclear assertion message fragment 'original one' in utils.py; "
        "it should be replaced with a clearer description."
    )