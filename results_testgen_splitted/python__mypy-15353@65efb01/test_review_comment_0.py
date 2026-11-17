import pytest

import mypy.typeops as typeops
from mypy.nodes import Argument, Block, FuncDef, Var
from mypy.types import AnyType, TypeOfAny


def test_callable_type_does_not_mutate_funcdef_is_static_for_dunder_new() -> None:
    """
    callable_type() must not mutate fdef.is_static for '__new__'.
    """
    # Build a minimal, valid FuncDef with one argument so callable_type can run.
    v = Var("self", AnyType(TypeOfAny.unannotated))
    arg = Argument(v, AnyType(TypeOfAny.unannotated), None, 0)
    fdef = FuncDef("__new__", [arg], Block([]))

    # Avoid needing a real TypeInfo/Instance fallback in this test.
    fdef.info = None
    fdef.is_static = False

    _ = typeops.callable_type(fdef, fallback=None)  # type: ignore[arg-type]

    assert (
        fdef.is_static is False
    ), "callable_type() must not mutate FuncDef.is_static for '__new__' (semantic analysis should set it)"