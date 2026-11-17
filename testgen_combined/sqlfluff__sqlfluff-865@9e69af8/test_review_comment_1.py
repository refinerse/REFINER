import pytest

from sqlfluff.core import Linter


def test_update_statement_uses_table_reference_segment_when_no_alias():
    """Verify UPDATE target table parses as TableReferenceSegment when unaliased.

    This reflects the review change to use:
      OneOf(TableReferenceSegment, AliasedTableReferenceSegment)
    rather than always AliasedTableReferenceSegment (alias optional).
    """
    sql = "UPDATE my_table SET col = 1"

    linter = Linter(dialect="ansi")
    parsed = linter.parse_string(sql)

    # parse_string() returns a ParsedString with a .tree attribute.
    tree = parsed.tree
    assert tree is not None, "Sanity check: Expected SQL to parse into a non-null parse tree."

    update_stmts = list(tree.recursive_crawl("update_statement"))
    assert update_stmts, "Expected the SQL to contain an 'update_statement' segment."

    update_stmt = update_stmts[0]

    # In the "after" version, the unaliased UPDATE target should be a direct
    # TableReferenceSegment child (cleaner parse), not an AliasedTableReferenceSegment.
    direct_table_refs = update_stmt.get_children("table_reference")
    assert (
        len(direct_table_refs) == 1
    ), "Expected UPDATE statement to have exactly one direct 'table_reference' child for the target table."

    target = direct_table_refs[0]
    assert target.__class__.__name__ == "TableReferenceSegment", (
        "Expected unaliased UPDATE target to parse as TableReferenceSegment. "
        "If it parses as AliasedTableReferenceSegment, it indicates the grammar is still "
        "routing unaliased tables through the 'aliased' segment with optional alias."
    )