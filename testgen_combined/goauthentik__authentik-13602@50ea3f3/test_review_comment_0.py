import re

MIGRATION_PATH = "/workspace/authentik/events/migrations/0009_remove_notificationtransport_webhook_mapping_and_more.py"


def test_migration_uses_renamefield_instead_of_remove_add_for_webhook_mapping():
    source = open(MIGRATION_PATH, "r", encoding="utf-8").read()

    # The reviewed style fix: this migration should preserve data by renaming the field,
    # not removing and re-adding it.
    assert "migrations.RenameField(" in source, (
        "Migration should use migrations.RenameField to rename 'webhook_mapping' to "
        "'webhook_mapping_body' (preserving data), not RemoveField+AddField."
    )

    # Ensure the rename is specifically webhook_mapping -> webhook_mapping_body
    rename_block = re.search(r"migrations\.RenameField\((?P<body>[\s\S]*?)\)\s*,", source)
    assert rename_block, (
        "Expected to find a migrations.RenameField(...) operation block in the migration file."
    )
    body = rename_block.group("body")
    assert 'old_name="webhook_mapping"' in body and 'new_name="webhook_mapping_body"' in body, (
        "migrations.RenameField must rename old_name='webhook_mapping' to new_name='webhook_mapping_body'."
    )

    # And it should NOT remove the original field (that would drop data).
    assert "migrations.RemoveField(" not in source, (
        "Migration must not include migrations.RemoveField for 'webhook_mapping'; "
        "it should be a RenameField instead."
    )