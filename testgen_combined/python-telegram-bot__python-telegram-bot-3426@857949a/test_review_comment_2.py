import re

import pytest


def test_send_invoice_default_protect_content_uses_kwargs_variable_name():
    """
    Review comment: rename loop variable `i` -> `kwargs`.

    This has no runtime behavior impact, so we assert it at source level:
    In tests/test_invoice.py, the generator that iterates over ({}, {"protect_content": False})
    must use `for kwargs in ...` and must not use `for i in ...`.
    """
    source = open("/workspace/tests/test_invoice.py", "r", encoding="utf-8").read()

    # Ensure we're looking at the relevant test by anchoring to its name
    assert (
        "async def test_send_invoice_default_protect_content" in source
    ), "Expected test_send_invoice_default_protect_content to exist in /workspace/tests/test_invoice.py"

    # The "after" code should contain `for kwargs in ({}, {"protect_content": False})`
    assert re.search(
        r"for\s+kwargs\s+in\s*\(\s*\{\s*\}\s*,\s*\{\s*['\"]protect_content['\"]\s*:\s*False\s*\}\s*\)",
        source,
        flags=re.DOTALL,
    ), (
        "Expected the generator expression in test_send_invoice_default_protect_content to use "
        "`for kwargs in ({}, {'protect_content': False})` (i.e., rename loop variable `i` -> `kwargs`)."
    )

    # The "before" code uses `for i in ...`; ensure that is not present anymore.
    assert not re.search(
        r"for\s+i\s+in\s*\(\s*\{\s*\}\s*,\s*\{\s*['\"]protect_content['\"]\s*:\s*False\s*\}\s*\)",
        source,
        flags=re.DOTALL,
    ), (
        "Found `for i in ({}, {'protect_content': False})` in test_send_invoice_default_protect_content; "
        "the review comment requires renaming `i` to `kwargs`."
    )