import re


def test_prompt_fileselect_external_error_message_is_user_friendly():
    source = open("/workspace/qutebrowser/mainwindow/prompt.py", encoding="utf-8").read()

    # The reviewed change replaces including the full object repr (`{self._prompt}`)
    # with only the class name (`{self._prompt.__class__.__name__}`) in the
    # CommandError message.
    assert (
        "f\"not {self._prompt.__class__.__name__}\"" in source
    ), (
        "Expected prompt_fileselect_external to raise a CommandError mentioning only "
        "the prompt class name (self._prompt.__class__.__name__) rather than the full "
        "prompt object repr (self._prompt)."
    )

    # Ensure the old, overly verbose message format is gone.
    assert (
        "not {self._prompt}" not in source
    ), (
        "Found old error message format using {self._prompt}, which is overly verbose "
        "and should have been replaced with {self._prompt.__class__.__name__}."
    )

    # Also ensure the message is the expected one, i.e. contains the specific wording.
    assert re.search(
        r"Can only launch external fileselect for FilenamePrompt,.*not\s+\{self\._prompt\.__class__\.__name__\}",
        source,
        flags=re.DOTALL,
    ), (
        "Expected the error message to be 'Can only launch external fileselect for "
        "FilenamePrompt, not <ClassName>' using __class__.__name__."
    )