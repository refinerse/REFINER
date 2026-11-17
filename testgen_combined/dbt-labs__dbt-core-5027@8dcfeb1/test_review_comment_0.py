import re


def test_resolve_metric_does_not_return_disabled_wrapper():
    source = open("/workspace/core/dbt/contracts/graph/manifest.py").read()

    # This test enforces the behavior change from the review:
    # metrics are *not* "yaml-only disabled resources" handled via DisabledLookup.
    #
    # Before: resolve_metric had scaffolding for "disabled" metrics and could return Disabled(...)
    # After: resolve_metric only returns the metric (if found) or None; no disabled lookup/wrapper.
    #
    # Since we cannot import the module in this environment, we assert against the
    # implementation text in resolve_metric to ensure it cannot return Disabled.
    m = re.search(
        r"def resolve_metric\([\s\S]*?\n\s*def resolve_doc\(",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, "Expected to find Manifest.resolve_metric definition in manifest.py"
    resolve_metric_block = m.group(0)

    assert (
        "disabled_lookup" not in resolve_metric_block
    ), "resolve_metric should not consult disabled_lookup (metrics are not resolved as disabled resources)"
    assert (
        "return Disabled(" not in resolve_metric_block
    ), "resolve_metric should not return Disabled(...) wrappers; it should return a metric or None"
    assert (
        "disabled:" not in resolve_metric_block
    ), "resolve_metric should not define a 'disabled' variable; it should only look up enabled metrics"