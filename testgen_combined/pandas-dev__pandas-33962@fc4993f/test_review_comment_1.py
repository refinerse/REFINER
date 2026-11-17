import re


def test_read_json_lines_nrows_avoids_split_into_list():
    """
    Verify that when lines=True and nrows is provided, implementation avoids
    `data.split("\\n")` + slicing (which loads all lines into memory) and instead
    uses an iterator-based approach (islice on a file-like/StringIO).

    This is a source-level test because importing pandas fails in this environment.
    """
    source = open("/workspace/pandas/io/json/_json.py", encoding="utf-8").read()

    # "Before" implementation did: data = ensure_str(self.data); data = data.split("\n"); if self.nrows: data = data[: self.nrows]
    # "After" implementation does: lines = list(islice(self.data, self.nrows)) when self.nrows is set.
    assert "elif self.lines:" not in source, (
        "Test expects updated control-flow structure `if self.lines:` in JsonReader.read; "
        "the old `elif self.lines:` structure indicates the pre-fix implementation."
    )

    # Ensure the optimized nrows path exists in JsonReader.read
    assert re.search(
        r"def read\(self\):.*?if self\.lines:.*?elif self\.nrows:\s*"
        r"lines\s*=\s*list\(islice\(self\.data,\s*self\.nrows\)\)",
        source,
        flags=re.S,
    ), (
        "JsonReader.read should, for lines=True and nrows provided (without chunksize), "
        "use `list(islice(self.data, self.nrows))` to avoid splitting the entire input."
    )

    # Ensure we are not doing the memory-heavy pattern `split` and slice by nrows in the lines branch
    assert not re.search(
        r"if self\.lines:.*?data\s*=\s*ensure_str\(self\.data\).*?"
        r"data\s*=\s*data\.split\(\"\\n\"\).*?"
        r"if self\.nrows:\s*data\s*=\s*data\[:\s*self\.nrows\]",
        source,
        flags=re.S,
    ), (
        "JsonReader.read should not implement nrows for lines=True via "
        "`data = data.split(\"\\n\"); data = data[: self.nrows]` because that "
        "requires loading all lines into memory."
    )