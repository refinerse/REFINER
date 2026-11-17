import black


def test_empty_line_tracker_subtracts_previous_after_not_at_bof() -> None:
    """
    The refactor moved the "don't insert empty lines at BOF" logic into
    EmptyLineTracker.maybe_empty_lines().

    A specific behavioral change in that refactor: maybe_empty_lines() now
    adjusts `before` by subtracting `previous_after` (and clamps BOF to 0)
    *inside* the tracker. Previously, maybe_empty_lines() always did
    `before -= self.previous_after`, which can make `before` negative.

    This test constructs a scenario where `_maybe_empty_lines()` returns
    before=0 for a line following an import, but `previous_after==1`.
    The old logic returns before=-1; the new logic returns before=0.
    """
    elt = black.EmptyLineTracker(is_pyi=False)

    # First line: an import statement. For module-level imports, `_maybe_empty_lines`
    # returns (before=0, after=1).
    import_line = black.Line()
    import_line.append(black.Leaf(black.token.NAME, "import"), preformatted=True)
    import_line.append(black.Leaf(black.token.NAME, "os"), preformatted=True)

    before1, after1 = elt.maybe_empty_lines(import_line)
    assert (before1, after1) == (0, 1), (
        "Sanity check: module-level import should not need blank lines before, "
        "and should request 1 blank line after."
    )

    # Second line: a simple assignment at top level. With an import directly above,
    # `_maybe_empty_lines()` returns (before=1, after=0) because it wants a blank
    # line between imports and non-imports. But since the import already requested
    # `after=1`, the tracker should subtract it and produce `before=0` (not -1 or 1).
    assign_line = black.Line()
    assign_line.append(black.Leaf(black.token.NAME, "x"), preformatted=True)
    assign_line.append(black.Leaf(black.token.EQUAL, "="), preformatted=True)
    assign_line.append(black.Leaf(black.token.NUMBER, "1"), preformatted=True)

    before2, after2 = elt.maybe_empty_lines(assign_line)

    assert before2 == 0, (
        "EmptyLineTracker.maybe_empty_lines() must subtract previous_after and "
        "never return a negative `before`. In the pre-refactor code, this scenario "
        "returns before=-1 due to unconditional `before -= previous_after`."
    )
    assert after2 == 0, "Assignments should not request empty lines after."