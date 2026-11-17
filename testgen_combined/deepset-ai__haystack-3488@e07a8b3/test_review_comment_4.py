import re


def test_parsr_uses_sys_maxsize_for_headline_level_sentinel():
    source_path = "/workspace/haystack/nodes/file_converter/parsr.py"
    source = open(source_path, "r", encoding="utf-8").read()

    assert "cur_lowest_headline_level = sys.maxsize" in source, (
        "Expected ParsrConverter._convert_table_element() to use `sys.maxsize` as the sentinel value for "
        "`cur_lowest_headline_level` to make intent explicit. "
        "This should replace the previous magic number (e.g. `1000`)."
    )

    # Ensure the old magic number isn't still used for this variable
    assert not re.search(r"cur_lowest_headline_level\s*=\s*1000\b", source), (
        "Found `cur_lowest_headline_level = 1000`, but the code should use `sys.maxsize` instead of a magic number."
    )

    assert re.search(r"^\s*import\s+sys\s*$", source, flags=re.MULTILINE), (
        "Expected `import sys` to be present since `sys.maxsize` is used."
    )