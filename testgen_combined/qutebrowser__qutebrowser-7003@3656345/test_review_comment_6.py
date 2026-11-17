import re


def test_prompt_fileselect_external_asserts_prompt_not_none():
    """Ensure prompt_fileselect_external asserts _prompt is not None before type check.

    This enforces the reviewed style change:
        assert self._prompt is not None
        if not isinstance(self._prompt, FilenamePrompt):
            ...
    """
    path = "/workspace/qutebrowser/mainwindow/prompt.py"
    source = open(path, "r", encoding="utf-8").read()

    # Grab the function body in a simple, robust way (no AST).
    m = re.search(
        r"def prompt_fileselect_external\(self\):(?P<body>.*?)(?:\n\s*def |\nclass |\Z)",
        source,
        flags=re.S,
    )
    assert m is not None, "Could not find prompt_fileselect_external in /workspace/qutebrowser/mainwindow/prompt.py"
    body = m.group("body")

    assert "assert self._prompt is not None" in body, (
        "prompt_fileselect_external should contain 'assert self._prompt is not None' "
        "to document/enforce that _prompt cannot be None in prompt mode."
    )

    # Ensure the old combined check is gone.
    assert "if not (self._prompt and isinstance(self._prompt, FilenamePrompt))" not in body, (
        "prompt_fileselect_external should not use the old combined check "
        "'if not (self._prompt and isinstance(...))'; it should assert non-None first."
    )

    # Ensure the assert comes before the isinstance check (ordering matters).
    assert_pos = body.find("assert self._prompt is not None")
    isinstance_pos = body.find("isinstance(self._prompt, FilenamePrompt)")
    assert isinstance_pos != -1, (
        "prompt_fileselect_external should check isinstance(self._prompt, FilenamePrompt) "
        "after asserting self._prompt is not None."
    )
    assert assert_pos < isinstance_pos, (
        "prompt_fileselect_external should assert self._prompt is not None before "
        "checking isinstance(self._prompt, FilenamePrompt)."
    )