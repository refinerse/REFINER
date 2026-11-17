import inspect

from gradio.components.textbox import Textbox


def test_textbox_text_align_default_is_none_for_rtl_precedence():
    """
    Style/API expectation: `rtl` should take precedence over `text_align`, which is
    reflected by making `text_align` default to None (so it can be derived from rtl).
    This test checks that the public constructor signature has text_align default None.
    """
    sig = inspect.signature(Textbox.__init__)
    assert "text_align" in sig.parameters, "Textbox.__init__ must accept a `text_align` parameter."

    text_align_param = sig.parameters["text_align"]
    assert (
        text_align_param.default is None
    ), "Expected Textbox.__init__ `text_align` default to be None so `rtl` can take precedence; got a non-None default."