import re


def test_finish_release_docstring_run_instructions_include_css_flag():
    source = open("/workspace/tools/finish_release.py", encoding="utf-8").read()

    # The file starts with a shebang, so the docstring is not at absolute start.
    # Find the first triple-quoted module docstring anywhere near the top.
    m = re.search(r'(?s)^[ \t]*(?:"""|\'\'\')(.+?)(?:"""|\'\'\')', source, re.MULTILINE)
    assert m is not None, (
        "Expected tools/finish_release.py to contain a top-level (module) docstring "
        "(a triple-quoted string near the top of the file)."
    )
    doc = m.group(1)

    expected_line = "python tools/finish_release.py --css <URL of code signing server>"
    assert expected_line in doc, (
        "The module docstring Run instructions should document the required --css argument.\n"
        f"Expected to find this exact line in the docstring:\n  {expected_line}"
    )

    # Ensure the Run section does not still document running without --css.
    # We scope this check to the Run section so other occurrences in the docstring
    # (or code) do not affect the test.
    run_section_match = re.search(r"(?s)\bRun:\s*(.+?)\n\s*\bTesting:", doc)
    assert run_section_match is not None, (
        "Expected the module docstring to contain a 'Run:' section followed by a 'Testing:' section."
    )
    run_section = run_section_match.group(1)

    assert "python tools/finish_release.py\n" not in run_section, (
        "The module docstring Run instructions should not tell users to run the script without --css."
    )