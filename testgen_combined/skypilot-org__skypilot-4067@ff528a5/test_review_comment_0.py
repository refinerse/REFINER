import re


def test_diamond_yaml_uses_downstream_not_dependencies():
    path = "/workspace/examples/dag/diamond.yml"
    source = open(path, "r", encoding="utf-8").read()

    # The review comment changed the DAG edge direction and renamed the YAML header:
    # from `dependencies` (predecessors) to `downstream` (successors).
    assert re.search(r"(?m)^\s*downstream\s*:\s*$", source), (
        "examples/dag/diamond.yml must define the DAG using a top-level "
        "'downstream:' mapping (edge direction style consistent with '>>'). "
        "Expected to find a line 'downstream:' in the pipeline header."
    )

    assert not re.search(r"(?m)^\s*dependencies\s*:\s*$", source), (
        "examples/dag/diamond.yml should not use the old 'dependencies:' header; "
        "it was renamed to 'downstream:' to fix edge direction consistency."
    )