import inspect
import re

import airflow.models.baseoperator as baseoperator


def test_chain_param_tasks_line_uses_prose_not_type_enumeration():
    """
    Structural doc change: Only the ':param tasks:' line should be prose-only
    (no type enumeration). The docstring may still contain ':type tasks:' with types.
    """
    doc = inspect.getdoc(baseoperator.chain)
    assert doc is not None, "chain() must have a docstring"

    # Ensure the exact prose line requested by the review is present.
    expected = ":param tasks: List of tasks or XComArgs to set dependencies"
    assert expected in doc, (
        "chain() docstring should contain the prose-only ':param tasks:' line. "
        f"Expected to find: {expected!r}"
    )

    # Extract just the ':param tasks:' line (ignore any ':type tasks:' lines).
    m = re.search(r"(?m)^\s*:param\s+tasks:\s*(.+?)\s*$", doc)
    assert m, "Could not locate a ':param tasks:' line in chain() docstring"
    param_line_text = m.group(1)

    # The 'before' version enumerates types in ':param tasks:'; the 'after' version does not.
    forbidden_in_param_line = ["airflow.models.BaseOperator", "airflow.models.XComArg", "List["]
    assert not any(tok in param_line_text for tok in forbidden_in_param_line), (
        "The ':param tasks:' line should be prose-only and must not enumerate types. "
        f"Found forbidden tokens in ':param tasks:' line: "
        f"{[t for t in forbidden_in_param_line if t in param_line_text]}. "
        f"Actual ':param tasks:' line text: {param_line_text!r}"
    )