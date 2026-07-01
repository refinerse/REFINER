import warnings

import pytest

from tests.helpers.utils import no_warning_call


def test_no_warning_call_match_uses_regex_on_original_message_object_not_str():
    class Message:
        def __init__(self, text: str):
            self.text = text

        def __str__(self) -> str:
            # This is intentionally NOT the actual message content.
            # The bug (before) stringifies the object and applies regex to this value.
            return "NOT_THE_MESSAGE"

        def __repr__(self) -> str:
            return f"Message(text={self.text!r})"

    msg_obj = Message("hello world")

    # Ensure no unrelated warnings interfere (the helper checks all recorded warnings)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Correct behavior (after): regex runs on the original object, so it won't match "hello world"
        # because the object is not a string and doesn't contain it for regex purposes, thus the warning
        # should be treated as "not matching" and no_warning_call should raise.
        with pytest.raises(
            AssertionError,
            match=r"was raised",
        ), no_warning_call(UserWarning, match=r"hello world"):
            warnings.warn(msg_obj, UserWarning)

    assert True, "no_warning_call should raise if the regex does not match the original warning message object."