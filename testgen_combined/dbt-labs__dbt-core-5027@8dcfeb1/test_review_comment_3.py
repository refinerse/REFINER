import pytest

from core.dbt.contracts.graph import metrics as metrics_mod


def test_resolved_metric_reference_requires_manifest_and_relation_and_has_parent_models():
    """
    The review discussion led to expanding ResolvedMetricReference so it can
    resolve parent metrics/models via manifest + Relation. This test asserts:
      1) The constructor accepts (node, manifest, Relation) without error.
      2) parent_models() exists and returns a dict with 'base' and 'derived' keys.

    Before: __init__ only accepted (node) and there was no parent_models().
    After: __init__ accepts (node, manifest, Relation) and parent_models() is implemented.
    """

    class DummyDependsOn:
        def __init__(self, nodes):
            self.nodes = nodes

    class DummyMetricNode:
        def __init__(self, name="revenue", package_name="pkg", type_="simple", depends=None):
            self.name = name
            self.package_name = package_name
            self.type = type_
            self.depends_on = depends or DummyDependsOn(nodes=[])

    class DummyManifest:
        def __init__(self):
            self.metrics = {}
            self.nodes = {}

    class DummyRelation:
        @classmethod
        def create(cls, database, schema, identifier):
            return f"{database}.{schema}.{identifier}"

    node = DummyMetricNode()
    manifest = DummyManifest()

    # This must succeed on the "after" code. On "before" code it raises TypeError
    # due to a different __init__ signature.
    ref = metrics_mod.ResolvedMetricReference(node, manifest, DummyRelation)

    assert hasattr(
        ref, "parent_models"
    ), "ResolvedMetricReference should implement parent_models() to support resolving metric relations via manifest"

    result = ref.parent_models()
    assert isinstance(result, dict) and "base" in result and "derived" in result, (
        "parent_models() should return a dict with 'base' and 'derived' keys; "
        f"got: {result!r}"
    )