# -*- coding: utf-8 -*-

import os


def test_qtpy_dependency_description_is_short_form():
    """
    Style check: the qtpy dependency description should be exactly
    'Abstraction layer for Python Qt bindings.' per review comment.
    """
    path = "/workspace/spyder/dependencies.py"
    assert os.path.exists(path), f"Expected Spyder dependencies module at {path}"

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    marker = "'modname': \"qtpy\""
    idx = source.find(marker)
    assert idx != -1, (
        "Could not locate the qtpy dependency entry (expected to find "
        f"{marker!r} in /workspace/spyder/dependencies.py)."
    )

    # Limit search to the qtpy dict block to avoid matching other dependencies.
    next_entry = source.find("'modname':", idx + 1)
    block = source[idx: next_entry if next_entry != -1 else len(source)]

    # Extract the exact features string content inside _("...").
    feat_key = "'features': _("
    feat_idx = block.find(feat_key)
    assert feat_idx != -1, (
        "Found qtpy dependency entry but could not find its 'features' field."
    )

    # Find opening and closing quote for _("...") content.
    open_paren = block.find("(", feat_idx)
    assert open_paren != -1, "Malformed qtpy 'features' field: missing '(' after _('"

    # Support both single and double quotes.
    qpos = None
    quote = None
    for q in ('"', "'"):
        p = block.find(q, open_paren + 1)
        if p != -1 and (qpos is None or p < qpos):
            qpos = p
            quote = q
    assert qpos is not None, (
        "Malformed qtpy 'features' field: could not find opening quote inside _('...')."
    )

    end_qpos = block.find(quote, qpos + 1)
    assert end_qpos != -1, (
        "Malformed qtpy 'features' field: could not find closing quote."
    )

    features = block[qpos + 1 : end_qpos]
    assert features == "Abstraction layer for Python Qt bindings.", (
        "The qtpy dependency description must be updated to exactly "
        "'Abstraction layer for Python Qt bindings.' (including the period). "
        f"Found: {features!r}"
    )