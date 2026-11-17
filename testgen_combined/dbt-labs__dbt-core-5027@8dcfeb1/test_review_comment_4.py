from dataclasses import MISSING, fields

import core.dbt.contracts.graph.parsed as parsed


def test_parsed_metric_does_not_expose_patch_like_resolution_method():
    """
    Style/API guard: metrics should not add a "patch" step method on ParsedMetric.
    The reviewed direction was that metrics need a resolution phase elsewhere,
    so ParsedMetric should not define `resolve_metric_references`.
    """
    assert hasattr(parsed, "ParsedMetric"), "Sanity check: ParsedMetric must exist"

    has_method = hasattr(parsed.ParsedMetric, "resolve_metric_references")
    assert (
        not has_method
    ), "ParsedMetric should not define `resolve_metric_references` (resolution should not be a 'patch' method on the node)."


def test_parsed_metric_has_required_sql_field_and_no_ratio_terms_field():
    """
    Public surface check:
      - ParsedMetric.sql is required (no dataclass default)
      - ParsedMetric no longer exposes a ratio_terms field
    """
    metric_fields = {f.name: f for f in fields(parsed.ParsedMetric)}

    assert "sql" in metric_fields, "ParsedMetric must have an `sql` field"

    sql_field = metric_fields["sql"]
    assert (
        sql_field.default is MISSING and sql_field.default_factory is MISSING
    ), "ParsedMetric.sql should be a required field (dataclasses.MISSING default), not Optional/with a default."

    assert (
        "ratio_terms" not in metric_fields
    ), "ParsedMetric should not expose a `ratio_terms` field after the refactor."