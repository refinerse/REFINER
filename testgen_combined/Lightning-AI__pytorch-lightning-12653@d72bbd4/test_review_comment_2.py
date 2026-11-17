import re
import pytest

from tests.helpers.utils import no_warning_call


def test_no_warning_call_uses_raw_warning_message_for_regex_search():
    """The regex search must run on the original warning message object, not on its str().

    We craft a warning payload object that is:
    - "string-like" enough for `re.Pattern.search()` to work on it directly
      (implements __len__ and __getitem__)
    - but whose __str__() intentionally hides the actual text.

    Correct behavior (after): re.search(payload) matches -> no_warning_call raises AssertionError.
    Incorrect behavior (before): re.search(str(payload)) does not match -> no_warning_call returns (no error).
    """

    class Payload:
        def __init__(self, text: str) -> None:
            self._text = text

        def __len__(self) -> int:
            return len(self._text)

        def __getitem__(self, item):
            return self._text[item]

        def __str__(self) -> str:
            # Hide the actual text so matching on str(payload) fails
            return "<hidden>"

    class CustomWarning(UserWarning):
        pass

    payload = Payload("needle is here")

    # Sanity check: regex matches payload directly but not its stringification
    pattern = re.compile(r"needle")
    assert pattern.search(payload), "Test setup error: regex should match the payload object directly."
    assert not pattern.search(str(payload)), "Test setup error: regex should NOT match str(payload)."

    # After fix: will find the match and raise because the warning WAS raised.
    # Before fix: will not find the match and will return without raising (test should fail).
    with pytest.raises(AssertionError, match=r"was raised"):
        with no_warning_call(expected_warning=CustomWarning, match=r"needle"):
            pytest.warns(CustomWarning, lambda: (_ for _ in ()).throw(CustomWarning(payload)))