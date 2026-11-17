import re


def test_gitattributes_uses_generated_attr_macro_for_linguist_generated():
    source = open("/workspace/.gitattributes", "r", encoding="utf-8").read()

    # The review change introduces a macro so generated files can be tagged with
    # just "generated" instead of repeating "linguist-generated=true diff=generated".
    assert (
        "[attr]generated linguist-generated=true diff=generated" in source
    ), "Expected a generated attributes macro: '[attr]generated linguist-generated=true diff=generated'"

    # Ensure at least one generated-file pattern uses the macro (ends with 'generated')
    # rather than spelling out the full attributes.
    assert re.search(r"(?m)^[^\n#].*\s+generated\s*$", source), (
        "Expected at least one pattern to use the 'generated' macro (line ending with 'generated'). "
        "This confirms generated files are tagged with the macro instead of repeating "
        "'linguist-generated=true diff=generated' on each line."
    )

    # And ensure no generated-file patterns still repeat the full linguist/diff attributes.
    assert "linguist-generated=true diff=generated" not in source.split(
        "[attr]generated linguist-generated=true diff=generated", 1
    )[1], (
        "After defining the '[attr]generated' macro, generated file patterns should not repeat "
        "'linguist-generated=true diff=generated' elsewhere in .gitattributes."
    )