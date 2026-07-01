import inspect

from mypy.nodes import MypyFile, SymbolTable, SymbolTableNode
from mypy.options import Options
from mypy.partially_defined import PossiblyUndefinedVariableVisitor


def _make_symtab_node(*, kind: int, node: object) -> SymbolTableNode:
    """Create SymbolTableNode in a way that works across mypy versions."""
    sig = inspect.signature(SymbolTableNode)
    kwargs = {"kind": kind, "node": node}
    if "type_override" in sig.parameters:
        kwargs["type_override"] = None
    if "module_public" in sig.parameters:
        kwargs["module_public"] = True
    if "module_hidden" in sig.parameters:
        kwargs["module_hidden"] = False
    if "cross_ref" in sig.parameters:
        kwargs["cross_ref"] = None
    return SymbolTableNode(**kwargs)  # type: ignore[arg-type]


def test_builtins_are_not_bulk_recorded_into_tracker_definitions() -> None:
    """
    Verifies the behavioral/perf change: PossiblyUndefinedVariableVisitor.__init__
    should NOT bulk-record all builtins as tracker definitions.

    This is observable by checking that, right after initialization, a builtin name
    (e.g. 'len') is still considered undefined by the tracker's global scope.

    Before version: builtins were recorded => is_undefined('len') == False.
    After version: builtins are not recorded => is_undefined('len') == True.
    """
    builtins_file = MypyFile([], [], False, "__builtins__")
    builtins_file.names = SymbolTable()
    builtins_file.names["len"] = _make_symtab_node(kind=0, node=None)

    names = SymbolTable()
    names["__builtins__"] = _make_symtab_node(kind=0, node=builtins_file)

    v = PossiblyUndefinedVariableVisitor(
        msg=None,  # type: ignore[arg-type]
        type_map={},
        options=Options(),
        names=names,
    )

    assert v.tracker.is_undefined(
        "len"
    ), "Builtins like 'len' should not be pre-recorded as defined in the tracker during visitor initialization."