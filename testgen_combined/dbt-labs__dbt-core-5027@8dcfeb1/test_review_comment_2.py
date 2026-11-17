import re


def test_metric_parser_no_longer_special_cases_ratio_type():
    """
    The review comment pushes back on teaching the metric parser about subtypes
    like 'ratio'. The merged code removes the `if unparsed.type == 'ratio':`
    special-case branch in MetricParser.parse_metric.
    """
    source = open("/workspace/core/dbt/parser/schemas.py", "r", encoding="utf-8").read()

    assert (
        "if unparsed.type == 'ratio':" not in source
    ), "MetricParser.parse_metric should not special-case the 'ratio' subtype via `if unparsed.type == 'ratio':`; subtype-specific behavior should not live in the parser."

    # Also ensure the new general rendering approach is present: model rendering is conditional on model not None
    assert (
        "if parsed.model is not None:" in source
    ), "Expected MetricParser.parse_metric to render model refs only when `parsed.model` is not None (general behavior for all metric types)."

    # Ensure SQL is always rendered from parsed.sql, not branch-specific and not using capture_macros=True here
    assert (
        "parsed.sql = get_rendered(" in source and "node=parsed" in source
    ), "Expected MetricParser.parse_metric to always render `parsed.sql` via get_rendered(..., node=parsed) (general behavior for all metric types)."

    # Guard against the old derived-metric plumbing remaining in the parser
    assert (
        re.search(r"\bparsed\.is_derived\s*=", source) is None
    ), "MetricParser.parse_metric should not set `parsed.is_derived` in the parser; this is part of the removed subtype-specific logic."