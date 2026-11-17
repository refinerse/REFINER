import pytest

from telegram import Chat, Update, User

import tests.test_update as ttu


def test_effective_sender_tests_assert_type_and_are_split_for_anonymous_cases():
    """
    Regression test for review request:
    Ensure that tests for Update.effective_sender explicitly assert the type
    (Chat vs User) for the relevant use cases, and that there are separate tests
    for anonymous vs non-anonymous cases.

    This should fail for the "before" code because it only asserts `sender.id == 1`
    and has no `isinstance(sender, Chat/User)` assertions.
    """
    source = open("/workspace/tests/test_update.py", encoding="utf-8").read()

    assert "def test_effective_sender_non_anonymous" in source, (
        "Expected a dedicated test `test_effective_sender_non_anonymous` to exist, "
        "separating the non-anonymous case for `effective_sender`."
    )
    assert "def test_effective_sender_anonymous" in source, (
        "Expected a dedicated test `test_effective_sender_anonymous` to exist, "
        "separating the anonymous case for `effective_sender`."
    )

    assert "isinstance(sender, Chat)" in source or "isinstance(sender,User)" in source or "isinstance(sender, User)" in source, (
        "Expected tests for `effective_sender` to explicitly assert the sender type via "
        "`assert isinstance(sender, Chat)` and/or `assert isinstance(sender, User)`."
    )

    # Functional sanity: effective_sender should indeed be Chat for channel posts and User for normal messages.
    # This ensures the test file's intent matches runtime behavior.
    channel_update = Update(update_id=1, channel_post=ttu.channel_post)
    sender = channel_update.effective_sender
    assert isinstance(sender, Chat), (
        "Runtime sanity check: for channel_post updates, `effective_sender` should be a Chat."
    )

    msg_update = Update(update_id=2, message=ttu.message)
    sender2 = msg_update.effective_sender
    assert isinstance(sender2, (Chat, User, type(None))), (
        "Runtime sanity check: `effective_sender` should be Chat/User/None depending on anonymity/use-case."
    )