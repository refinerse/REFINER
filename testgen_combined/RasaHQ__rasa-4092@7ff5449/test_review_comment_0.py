import inspect

import rasa.core.events.__init__ as events


def test_useruttered_from_parse_data_has_type_hints_for_key_params():
    """Ensure UserUttered._from_parse_data has explicit type hints for key params."""
    sig = inspect.signature(events.UserUttered._from_parse_data)

    text_ann = sig.parameters["text"].annotation
    parse_data_ann = sig.parameters["parse_data"].annotation

    assert (
        text_ann is events.Text
    ), f"Expected 'text' parameter to be annotated as Text, but got {text_ann!r}."
    assert (
        parse_data_ann == events.Dict[events.Text, events.Any]
    ), (
        "Expected 'parse_data' parameter to be annotated as Dict[Text, Any], "
        f"but got {parse_data_ann!r}."
    )

    assert "message_id" in sig.parameters, (
        "Expected UserUttered._from_parse_data to accept 'message_id' parameter "
        "(required to pass message IDs through parsing)."
    )
    message_id_ann = sig.parameters["message_id"].annotation
    assert (
        message_id_ann == events.Optional[events.Text]
    ), f"Expected 'message_id' parameter to be annotated as Optional[Text], but got {message_id_ann!r}."