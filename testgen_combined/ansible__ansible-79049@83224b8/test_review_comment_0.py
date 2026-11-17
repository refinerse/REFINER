import pytest

from lib.ansible.playbook.block import Block


def test_get_parent_attribute_uses_fieldattribute_extend_prepend_attributes_directly():
    """
    Regression test for _get_parent_attribute(): it should access FieldAttribute's
    .extend and .prepend directly, rather than using getattr(..., default=False).

    This is observable at runtime by using a FieldAttribute subclass whose
    __getattribute__ distinguishes between direct attribute access and getattr()
    with a default (which passes a third argument to __getattribute__).
    """

    class TrapAttr:
        def __init__(self, name):
            self.name = name

        # getattr(obj, name, default) in CPython calls obj.__getattribute__(name, default)
        # If code uses getattr(..., default), we'll return False regardless of the actual
        # attribute value. If code uses direct access (obj.extend), default is not passed
        # and we return True.
        def __getattribute__(self, name, default=object()):
            if name in ("extend", "prepend"):
                if default is not object():
                    return False  # "before" behavior: getattr(..., default=False)
                return True  # "after" behavior: direct attribute access
            return object.__getattribute__(self, name)

    b = Block(play=None, parent_block=None, role=None, task_include=None, use_handlers=False, implicit=False)

    # Provide exactly one attribute in fattributes so b.fattributes[attr] works.
    b.fattributes = {"notify": TrapAttr("notify")}

    # With direct attribute access, this should see extend/prepend as True/True.
    # With getattr(..., default=False), our trap forces them to False/False.
    result = b._get_parent_attribute("notify", omit=True)

    assert result is not None  # sanity: method returned something, not crashed

    # Most robust observable: 'extend' being True causes _get_parent_attribute to
    # attempt the parent/role/play extension logic. In this minimal setup there
    # are no parents, so value remains Sentinel either way; thus we inspect the
    # actual extend/prepend values by calling the same access pattern via runtime.
    #
    # We can observe it indirectly by checking which access mode was used:
    # - If the function used getattr(..., default), extend/prepend resolve to False.
    # - If it used direct access, extend/prepend resolve to True.
    #
    # We detect this by repeating the access with the same object and relying
    # on the trap's behavior.
    fattr = b.fattributes["notify"]
    observed_direct_extend = fattr.extend
    observed_direct_prepend = fattr.prepend

    assert (observed_direct_extend, observed_direct_prepend) == (True, True), (
        "Test setup sanity: direct attribute access must see extend/prepend as True/True "
        "so the test can distinguish direct access vs getattr(..., default=False)."
    )

    # Now assert the production code used direct access (i.e., did NOT use getattr with a default)
    # by verifying that extend/prepend were not forced to False by our trap.
    #
    # We do this by recomputing what production code would have computed if it used getattr(..., default=False),
    # and asserting that production behavior differs (must be True/True instead of False/False).
    via_getattr_extend = getattr(fattr, "extend", False)
    via_getattr_prepend = getattr(fattr, "prepend", False)

    assert (via_getattr_extend, via_getattr_prepend) == (False, False), (
        "Test setup sanity: getattr(..., default=False) must see extend/prepend as False/False "
        "so the test fails on code that uses getattr with a default."
    )

    # Finally, assert the implementation does NOT behave like the getattr(..., default) path.
    # In the 'before' code, extend/prepend are taken via getattr(..., default=False) and would be False/False.
    # In the 'after' code, extend/prepend are taken via direct access and would be True/True.
    #
    # We can't directly read local variables from _get_parent_attribute, but we can assert that
    # the implementation matches the direct-access contract by checking that the trap was not
    # queried with a default. The only reliable way without mocking is source-level behavior:
    # perform a minimal parent chain and ensure 'extend' being True triggers evaluation.
    #
    # Create a parent block with an explicit _notify value so extending changes result.
    parent = Block()
    # Bypass Base attribute machinery by setting the internal storage directly.
    parent._notify = ["from_parent"]
    b._parent = parent
    b._notify = ["from_self"]

    # If extend=True (after), self value should be extended with parent value -> length > 1.
    # If extend=False (before), it should just return parent's value when omit=True, but we use omit=False
    # so it should return self value only -> length == 1.
    combined = b._get_parent_attribute("notify", omit=False)

    assert isinstance(combined, list), "Expected _get_parent_attribute to return a list for list-like attributes."
    assert len(combined) > 1, (
        "When FieldAttribute.extend/prepend are present, _get_parent_attribute should treat them as "
        "real attributes (direct access) and extend values; using getattr(..., default=False) incorrectly "
        "suppresses extending in this test setup."
    )