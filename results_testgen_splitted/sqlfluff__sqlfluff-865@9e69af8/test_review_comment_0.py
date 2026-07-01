import re


def test_update_fixture_has_single_table_reference_level():
    """Ensure update.yml fixture does not contain a nested table_reference under table_reference.

    The reviewed style issue was a mistakenly nested structure:
        table_reference:
          table_reference:
            identifier: table_name

    The desired structure is:
        table_reference:
          identifier: table_name
    """
    path = "/workspace/test/fixtures/parser/ansi/update.yml"
    source = open(path, "r", encoding="utf-8").read()

    # Detect the specific undesired nested pattern with indentation-aware regex.
    nested_pattern = re.compile(
        r"(?m)^[ \t]*table_reference:\s*\n[ \t]*table_reference:\s*\n",
    )

    assert not nested_pattern.search(source), (
        "Fixture contains a nested 'table_reference' mapping under 'table_reference', "
        "which is the style issue mentioned in the review. Expected a single "
        "'table_reference:' level with 'identifier: table_name' directly beneath it."
    )