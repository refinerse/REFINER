import sys

# The execution environment invokes pytest with `--no-header`, but the pytest
# version available here doesn't recognize that option. Remove it before pytest
# parses CLI args. This must happen before importing pytest.
sys.argv = [a for a in sys.argv if a != "--no-header"]

import pytest  # noqa: E402

from rasa.core.events import UserUttered  # noqa: E402


def test_user_uttered_from_parse_data_preserves_message_id_and_metadata():
    parse_data = {"intent": {"name": "greet"}, "entities": []}

    event = UserUttered._from_parse_data(
        text="hi",
        parse_data=parse_data,
        timestamp=123,
        input_channel="rest",
        message_id="mid-123",
        metadata={"foo": "bar"},
    )

    assert (
        event.message_id == "mid-123"
    ), "UserUttered._from_parse_data should set `message_id` on the created event."
    assert event.metadata == {
        "foo": "bar"
    }, "UserUttered._from_parse_data should set `metadata` on the created event."
    assert event.parse_data.get("message_id") == "mid-123", (
        "UserUttered constructed via _from_parse_data should preserve message_id in "
        "`parse_data` (used for persistence/serialization)."
    )
    assert event.parse_data.get("metadata") == {"foo": "bar"}, (
        "UserUttered constructed via _from_parse_data should preserve metadata in "
        "`parse_data` (used for persistence/serialization)."
    )