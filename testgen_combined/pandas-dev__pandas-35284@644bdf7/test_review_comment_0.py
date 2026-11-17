def test_latex_longtable_begin_does_not_duplicate_position_assignment_block():
    # This is a pure style regression test: the "before" version accidentally
    # duplicated the `if self.position is None: ... else: ...` block in
    # `_write_longtable_begin`. That duplication has no runtime effect, so we
    # must assert on the source.
    source = open("/workspace/pandas/io/formats/latex.py", encoding="utf-8").read()

    # Count the number of occurrences of the exact conditional line in the file.
    # In the buggy "before" version, the duplicated block results in 2 occurrences
    # (within _write_longtable_begin). In the fixed "after" version, it is 1.
    needle = "if self.position is None:\n            position_ = \"\""
    count = source.count(needle)

    assert (
        count == 1
    ), (
        "Expected exactly one `if self.position is None:` block assigning `position_` "
        "in pandas/io/formats/latex.py (duplicate lines were present before the fix). "
        f"Found {count} occurrences of the position-assignment block."
    )