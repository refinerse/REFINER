# This test file must be compatible with PyPy/CPython and various pytest
# assertion rewrite behaviors. Keep it minimal and avoid any constructs that
# could trigger rewriting issues in some environments.

def test_paramiko_dependency_append_is_multiline_block_style():
    path = "/workspace/spyder/dependencies.py"
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    # The review requested converting the Windows paramiko dependency append
    # from a one-liner dict to a multi-line, parenthesized call.
    assert "DEPENDENCIES_BASE.append(\n" in source, (
        "Expected a multi-line `DEPENDENCIES_BASE.append(` call (with a newline "
        "after the opening parenthesis) as requested in the review comment."
    )

    assert "DEPENDENCIES_BASE.append({'modname': \"paramiko\"" not in source, (
        "The paramiko dependency append is still written as a one-line dict. "
        "It should be converted to the multi-line block style."
    )

    # Ensure the multi-line append block actually corresponds to paramiko.
    idx = source.find("DEPENDENCIES_BASE.append(\n")
    assert idx != -1, "Expected to find a multi-line `DEPENDENCIES_BASE.append(` call."

    snippet = source[idx: idx + 800]
    assert ("'modname': \"paramiko\"" in snippet) or ("'modname': 'paramiko'" in snippet), (
        "Expected the multi-line `DEPENDENCIES_BASE.append(` block to include the "
        "paramiko dependency dictionary."
    )