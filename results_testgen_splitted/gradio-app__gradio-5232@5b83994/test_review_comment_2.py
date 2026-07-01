import inspect

import gradio.components.radio as radio_mod


def test_radio_choices_docstring_uses_can_also_tuple_phrase():
    """
    Style regression test: the `choices` parameter docstring for gradio.components.radio.Radio.__init__
    should say "can also be a tuple" (not the ungrammatical "also be a tuple").
    """
    doc = inspect.getdoc(radio_mod.Radio.__init__) or ""
    assert (
        "An option can also be a tuple of the form (name, value)" in doc
    ), (
        "Expected Radio.__init__ docstring to describe choices as: "
        "'An option can also be a tuple of the form (name, value)'. "
        "This ensures the reviewed style/grammar fix is present."
    )