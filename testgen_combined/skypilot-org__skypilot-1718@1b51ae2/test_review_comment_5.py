import pytest


def test_lambda_node_provider_uses_metadata_get_set_api():
    """Ensure LambdaNodeProvider uses Metadata.get()/set() rather than
    dict-like __getitem__/__setitem__/exists(), per the review change.

    This is intentionally a source-level behavioral contract test because
    exercising LambdaNodeProvider at runtime would require real Lambda Cloud
    access and SSH.
    """
    path = "/workspace/sky/skylet/providers/lambda_cloud/node_provider.py"
    source = open(path, "r", encoding="utf-8").read()

    assert "self.metadata.get(" in source, (
        "Expected LambdaNodeProvider to use Metadata.get(node_id) to retrieve "
        "metadata (returning None if missing), instead of dict-like "
        "self.metadata[node_id]."
    )
    assert "self.metadata.set(" in source, (
        "Expected LambdaNodeProvider to use Metadata.set(node_id, value) to "
        "write metadata, instead of dict-like self.metadata[node_id] = value."
    )

    # These old patterns should be removed after the refactor.
    assert "self.metadata.exists(" not in source, (
        "Metadata.exists() should no longer be used; missing keys should be "
        "handled via Metadata.get() returning None."
    )
    assert "self.metadata[" not in source, (
        "Dict-like metadata access (self.metadata[...]) should no longer be "
        "used; use Metadata.get()/set() for clarity and dict API consistency."
    )