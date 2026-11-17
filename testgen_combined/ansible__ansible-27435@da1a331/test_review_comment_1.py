import pytest

import lib.ansible.modules.cloud.amazon.elb_classic_lb_facts as mod


def test_module_returns_key_named_elbs_not_elb_classic_facts():
    """
    The review comment indicates the change should NOT alter the module's returned results.
    The fix restores the return key to 'elbs' (as used in examples/docs), rather than the
    accidental 'elb_classic_facts'.

    This test enforces that the module's declared RETURN documentation exposes 'elbs:'.
    It fails on the before version (which documents 'elb_classic_facts:') and passes on
    the after version (which documents 'elbs:').
    """
    return_doc = getattr(mod, "RETURN", "")
    assert isinstance(return_doc, str) and return_doc.strip(), "Module should define a non-empty RETURN docstring."

    assert "elbs:" in return_doc, (
        "Module should return results under key 'elbs' (and document it in RETURN). "
        "Found RETURN that does not contain 'elbs:'."
    )
    assert "elb_classic_facts:" not in return_doc, (
        "Module should not return/document results under the key 'elb_classic_facts' "
        "(this was an unintended behavior change)."
    )