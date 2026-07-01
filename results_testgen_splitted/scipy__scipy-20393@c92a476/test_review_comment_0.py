import re


def test_newdoc_beta_entries_use_raw_triple_quoted_strings():
    source = open("/workspace/scipy/special/_add_newdocs.py", encoding="utf-8").read()

    # The review comment requests that these docstrings be raw strings because
    # they contain backslashes (e.g. "\leq") that would otherwise be interpreted
    # as escape sequences. Verify that the "_beta_pdf" and "_beta_ppf" entries
    # passed to add_newdoc use r"""...""" (not plain """...""").
    for name in ("_beta_pdf", "_beta_ppf"):
        # Find the add_newdoc call block for this name and capture the opening
        # triple-quoted string prefix (either r""" or """).
        m = re.search(
            rf'add_newdoc\(\s*"{re.escape(name)}"\s*,\s*(r?)"""',
            source,
            flags=re.MULTILINE,
        )
        assert m is not None, f"Expected to find add_newdoc call for {name!r} in /workspace/scipy/special/_add_newdocs.py"
        prefix = m.group(1)
        assert prefix == "r", (
            f"Docstring passed to add_newdoc for {name!r} must be a raw string (r\"\"\"...\"\"\") "
            f"to preserve backslashes in Sphinx math markup; found a non-raw triple-quoted string."
        )