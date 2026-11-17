import re


def test_team_live_events_columns_uses_textfield_not_charfield():
    source = open("/workspace/posthog/models/team/team.py").read()

    # Extract the live_events_columns field definition line (single line in this file)
    match = re.search(r"^\s*live_events_columns\s*:\s*ArrayField\s*=\s*(.+)$", source, flags=re.MULTILINE)
    assert match is not None, "Expected Team model to define `live_events_columns`, but it was not found."

    definition = match.group(1)

    assert "ArrayField(" in definition, "Expected `live_events_columns` to be an ArrayField definition."
    assert "models.TextField()" in definition, (
        "Expected `live_events_columns` to use `ArrayField(models.TextField(), ...)` to avoid max_length limits, "
        "but it does not. (It may still be using `models.CharField(max_length=...)`.)"
    )
    assert "models.CharField" not in definition, (
        "Expected `live_events_columns` not to use `models.CharField(...)`; it should use `models.TextField()` instead."
    )