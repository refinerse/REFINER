import pytest

from telegram import Chat, Message, Update


def test_effective_sender_includes_sender_chat_for_channel_post():
    """
    Regression test for Update.effective_sender:
    For channel posts, effective_sender should consider message.sender_chat (the channel chat),
    not fall back to effective_user (which is None for channel posts).
    """
    channel_chat = Chat(id=-100123456789, type=Chat.CHANNEL, title="Test Channel")

    channel_post = Message(
        message_id=1,
        date=0,
        chat=channel_chat,
        sender_chat=channel_chat,
        text="hello from channel",
    )

    update = Update(update_id=42, channel_post=channel_post)

    assert (
        update.effective_sender == channel_chat
    ), "Update.effective_sender must return channel_post.sender_chat for channel_post updates"