import re


def test_migration_docs_allow_population_by_field_name_mapping_mentions_both_names():
    source = open("/workspace/docs/migration.md", encoding="utf-8").read()

    # We want to enforce the style change in the migration docs:
    # `allow_population_by_field_name` should map to `populate_by_name`
    # and also mention `validate_by_name` starting in v2.11.
    expected_line_re = re.compile(
        r"^\s*\*\s*`allow_population_by_field_name`\s*→\s*`populate_by_name`\s*"
        r"\(or\s*`validate_by_name`\s*starting\s*in\s*v2\.11\)\s*$",
        re.MULTILINE,
    )
    assert expected_line_re.search(source), (
        "docs/migration.md should describe the rename as:\n"
        "  * `allow_population_by_field_name` → `populate_by_name` (or `validate_by_name` starting in v2.11)\n"
        "This ensures the migration guide reflects both the current name and the v2.11+ name."
    )

    # Also ensure we didn't leave the old/incorrect simplified mapping in place.
    incorrect_line_re = re.compile(
        r"^\s*\*\s*`allow_population_by_field_name`\s*→\s*`validate_by_name`\s*$",
        re.MULTILINE,
    )
    assert not incorrect_line_re.search(source), (
        "docs/migration.md should not list only:\n"
        "  * `allow_population_by_field_name` → `validate_by_name`\n"
        "It should mention `populate_by_name` with the parenthetical note about v2.11."
    )