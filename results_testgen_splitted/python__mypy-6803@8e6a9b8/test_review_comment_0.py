import pytest

from mypy import message_registry
from mypy.checker import TypeChecker
from mypy.errors import Errors
from mypy.nodes import Block, ClassDef, MypyFile
from mypy.options import Options
from mypy.types import AnyType, NoneType, TypeOfAny


def test_check_subtype_assignment_msg_with_non_instances_does_not_crash() -> None:
    """
    Regression test for the reviewed change in TypeChecker.check_subtype:

    BEFORE (buggy): when msg == INCOMPATIBLE_TYPES_IN_ASSIGNMENT, check_subtype called
        append_invariance_notes([], subtype, supertype)
    unconditionally inside the label block, even if subtype/supertype weren't Instances.
    This can raise at runtime (append_invariance_notes expects Instances).

    AFTER (fixed): check_subtype only calls append_invariance_notes if BOTH subtype and
    supertype are Instances. Therefore, for non-Instance types, check_subtype must not crash.

    This test must FAIL on the "before" code by raising an exception, and PASS on the "after"
    code by returning False cleanly.
    """
    options = Options()

    tree = MypyFile([], [], False, set())
    tree._fullname = "__main__"
    tree.path = "__main__"
    tree.names = {}

    errors = Errors(options)
    modules = {"__main__": tree}

    checker = TypeChecker(
        errors=errors,
        modules=modules,
        options=options,
        tree=tree,
        path="__main__",
        plugin=None,  # type: ignore[arg-type]
    )

    errors.set_file("__main__", "__main__")

    # Use non-Instance types that are NOT in a subtype relation so we reliably go down the error path.
    subtype = NoneType()
    supertype = AnyType(TypeOfAny.special_form)

    ctx = ClassDef("C", Block([]))

    try:
        ok = checker.check_subtype(
            subtype=subtype,
            supertype=supertype,
            context=ctx,
            msg=message_registry.INCOMPATIBLE_TYPES_IN_ASSIGNMENT,
            subtype_label="expression has type",
            supertype_label="variable has type",
        )
    except Exception as e:  # pragma: no cover
        pytest.fail(
            "check_subtype must not call append_invariance_notes for non-Instance types "
            "(it should guard with isinstance(subtype, Instance) and isinstance(supertype, Instance)). "
            f"Unexpected exception: {type(e).__name__}: {e}"
        )

    assert ok is False, (
        "Expected check_subtype to report an incompatibility (return False) for NoneType <: AnyType, "
        "and to do so without crashing when using INCOMPATIBLE_TYPES_IN_ASSIGNMENT."
    )