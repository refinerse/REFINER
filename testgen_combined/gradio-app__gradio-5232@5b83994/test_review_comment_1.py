import gradio.components.checkboxgroup as cbg


def test_checkboxgroup_example_inputs_returns_list_for_raw_and_serialized():
    """
    CheckboxGroup is a multi-select component, so its example inputs should be a list
    of selected values (even if only one is selected). The "before" code returned a
    scalar, while the "after" code returns a one-item list.
    """
    comp = cbg.CheckboxGroup(choices=[("A label", "A"), ("B label", "B")])
    examples = comp.example_inputs()

    assert "raw" in examples and "serialized" in examples, (
        "example_inputs() must return dict containing 'raw' and 'serialized' keys."
    )

    assert isinstance(examples["raw"], list), (
        "CheckboxGroup.example_inputs()['raw'] should be a list (multi-select), "
        f"but got {type(examples['raw']).__name__} with value {examples['raw']!r}."
    )
    assert isinstance(examples["serialized"], list), (
        "CheckboxGroup.example_inputs()['serialized'] should be a list (multi-select), "
        f"but got {type(examples['serialized']).__name__} with value {examples['serialized']!r}."
    )

    assert examples["raw"] == ["A"], (
        "CheckboxGroup.example_inputs()['raw'] should be a one-item list containing the first "
        f"choice value. Expected ['A'], got {examples['raw']!r}."
    )
    assert examples["serialized"] == ["A"], (
        "CheckboxGroup.example_inputs()['serialized'] should be a one-item list containing the first "
        f"choice value. Expected ['A'], got {examples['serialized']!r}."
    )