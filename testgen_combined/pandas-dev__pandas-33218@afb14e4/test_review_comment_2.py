# test_groupby_docstring_deprecated_newline.py
import re


def test_groupby_docstring_deprecated_directive_has_blank_line_and_correct_syntax():
    source = open("/workspace/pandas/core/generic.py", encoding="utf-8").read()

    m = re.search(
        r"_shared_docs\[\s*[\"']groupby[\"']\s*\]\s*=\s*([\"']{3})(?P<doc>.*?)(\1)",
        source,
        flags=re.DOTALL,
    )
    assert (
        m is not None
    ), "Could not find the _shared_docs['groupby'] docstring block in /workspace/pandas/core/generic.py"

    doc = m.group("doc")

    assert (
        "otherwise return a consistent type.\n\n            .. deprecated:: 1.1.0\n\n"
        in doc
    ), (
        "Expected groupby docstring to have a blank line before and after the "
        "reST deprecation directive for the 'squeeze' parameter, i.e.\n\n"
        "    otherwise return a consistent type.\n"
        "    <blank line>\n"
        "            .. deprecated:: 1.1.0\n"
        "    <blank line>\n"
        "but this exact pattern was not found."
    )

    assert (
        "otherwise return a consistent type.\n            deprecated:: 1.1.0" not in doc
    ), (
        "Found 'deprecated:: 1.1.0' without the leading '.. ' and without a blank "
        "line before it in the groupby docstring. It should be written as a proper "
        "reST directive and separated by blank lines."
    )