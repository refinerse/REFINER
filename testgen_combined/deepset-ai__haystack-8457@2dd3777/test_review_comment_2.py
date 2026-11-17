import re


def test_docx_table_format_enum_is_docx_specific_and_superfluous_comment_removed():
    source = open("/workspace/haystack/components/converters/docx.py", encoding="utf-8").read()

    assert (
        "class DOCXTableFormat(Enum):" in source
    ), "Expected a DOCX-specific enum named DOCXTableFormat to be defined."

    assert (
        "class TableFormat(Enum):" not in source
    ), "Did not expect a generic enum named TableFormat; it should be renamed to DOCXTableFormat."

    # The review comment was about removing a superfluous comment in from_dict.
    assert (
        "Convert the table_format string back to enum before passing to the constructor" not in source
    ), "Expected the superfluous explanatory comment in from_dict() to be removed."

    # Ensure from_dict converts init_parameters['table_format'] using DOCXTableFormat.from_str(...)
    pattern = re.compile(
        r'def from_dict\(cls, data: Dict\[str, Any\]\) -> "DOCXToDocument":.*?'
        r'if "table_format" in data\["init_parameters"\]:\s*'
        r'data\["init_parameters"\]\["table_format"\]\s*=\s*DOCXTableFormat\.from_str\(',
        re.DOTALL,
    )
    assert pattern.search(source), (
        "Expected DOCXToDocument.from_dict() to convert data['init_parameters']['table_format'] "
        "via DOCXTableFormat.from_str(...) without extra guard/comment."
    )