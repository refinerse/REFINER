import pytest

from gradio.components.checkboxgroup import CheckboxGroup


def test_checkboxgroup_example_inputs_returns_list_of_values():
    """
    CheckboxGroup examples-format expects a List[...] of values to be checked.
    example_inputs() should therefore return a single-element list containing the
    first choice's *value* (not a scalar), for both raw and serialized.
    """
    cbg = CheckboxGroup(choices=[("Displayed A", "a"), ("Displayed B", "b")])
    examples = cbg.example_inputs()

    assert examples["raw"] == ["a"], (
        "CheckboxGroup.example_inputs()['raw'] must be a list containing the first "
        "choice's value (e.g. ['a']) so API docs example snippets work as expected."
    )
    assert examples["serialized"] == ["a"], (
        "CheckboxGroup.example_inputs()['serialized'] must be a list containing the first "
        "choice's value (e.g. ['a']), matching the examples-format for CheckboxGroup."
    )