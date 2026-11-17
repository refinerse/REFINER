import re


def _get_local_hook_block(yaml_text: str, hook_id: str) -> str:
    """
    Extract the block corresponding to a local hook `-   id: <hook_id>`
    up to (but not including) the next hook id entry.
    """
    m = re.search(rf"(?m)^\s*-\s*id:\s*{re.escape(hook_id)}\s*$", yaml_text)
    assert m, f"Expected to find a local pre-commit hook with id '{hook_id}'"

    start = m.start()
    rest = yaml_text[m.end() :]
    next_m = re.search(r"(?m)^\s*-\s*id:\s*", rest)
    end = (m.end() + next_m.start()) if next_m else len(yaml_text)
    return yaml_text[start:end]


def test_cython_casting_hook_entry_is_single_quoted_one_liner_and_has_files_filter():
    source = open("/workspace/.pre-commit-config.yaml", encoding="utf-8").read()
    block = _get_local_hook_block(source, "cython-casting")

    assert "entry: '[a-zA-Z0-9*]> '" in block, (
        "The cython-casting pre-commit hook should use a single-line, quoted entry "
        "with a literal trailing space: entry: '[a-zA-Z0-9*]> '. "
        "This avoids YAML parsing issues with unquoted regex escapes like \\s."
    )
    assert "entry: |" not in block, (
        "The cython-casting hook entry should not be a multiline block scalar (entry: |); "
        "it should be a single quoted line."
    )

    # In the YAML file, backslashes are escaped, so the line contains literal '\.'
    assert re.search(r"(?m)^\s*files:\s*\(\\\.pyx\|\\\.pxi\.in\)\$\s*$", block), (
        r"The cython-casting hook should restrict files to Cython sources via "
        r"files: (\.pyx|\.pxi.in)$ (as written in the YAML, this appears as "
        r"(\\.pyx|\\.pxi.in)$)."
    )