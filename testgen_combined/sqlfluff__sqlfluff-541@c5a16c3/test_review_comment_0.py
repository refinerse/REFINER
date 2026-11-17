import re


def test_templatedfile_docstring_uses_templated_str_not_full_templated():
    """Verify docstring style: refer to `templated_str`, not the old `full_templated` name."""
    source = open("/workspace/src/sqlfluff/core/templaters/base.py").read()

    assert (
        "If no full_templated is provided" not in source
    ), (
        "TemplatedFile.__init__ docstring still references `full_templated`. "
        "The review comment requested using `templated_str` instead."
    )

    # Also require the corrected wording to be present to avoid a false pass by deletion.
    assert re.search(r"If no templated_str is provided", source), (
        "Expected TemplatedFile.__init__ docstring to reference `templated_str` "
        "(e.g. 'If no templated_str is provided...'), but it was not found."
    )