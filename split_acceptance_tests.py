#!/usr/bin/env python3
"""Split generated acceptance tests into per-assertion sub-tests.

Motivation
----------
Each generated test file in ``testgen_combined/<instance>/`` usually holds a
single ``def test_*`` function that performs several assertions in sequence.
Under pytest, the *first* failing assertion aborts the whole function, so the
report only ever tells us "this function failed" -- we never learn how many of
the remaining checks would have passed. We want a finer-grained report:
how many independent checks pass / fail.

This script rewrites each such function into one function *per top-level
assertion*, so pytest reports each check independently (e.g. ``3 passed,
1 failed`` instead of a single ``FAILED``).

The splitting heuristic
-----------------------
We operate on the *top-level statements* of every module-level ``def test_*``
function. A top-level statement is classified as either:

* a **check** -- it contains (directly or nested) an assertion-like construct:
  a bare ``assert``, a ``with pytest.raises(...)``, ``self.assertRaises(...)``,
  or a call to ``self.assert*`` / ``*.fail`` / ``np.testing.assert_*``; or
* **setup** -- anything else (imports, assignments, monkeypatch calls, helper
  ``def``/``for``/``with`` blocks that perform no assertion).

For each check at top-level position ``j`` we emit a new function whose body is
*all setup statements before ``j``* followed by *that single check*. Prior
checks are dropped, so a failing check no longer blocks the later ones, while
every assignment / fixture-setup the check depends on is faithfully replayed.

Why this is "wise" rather than naive line-splitting
----------------------------------------------------
Two safety rules keep a split from changing test meaning (which would break the
fail-on-head / pass-on-merged property the validator checks):

1. **Compound checks stay atomic.** When several asserts live inside one
   top-level block (e.g. all inside ``with tempfile.TemporaryDirectory():`` or
   inside a ``for`` loop, or a ``with pytest.raises() as e`` followed by
   ``assert ... e``), that block is a *single* top-level check and is emitted
   whole. We never reach inside a compound statement to pull asserts out.

2. **No dropped bindings.** If any check statement *binds a name* (``as`` var,
   walrus, assignment, loop var) that a later statement uses, splitting could
   lose that binding. In that case we refuse to split the function and copy it
   through unchanged.

Functions with 0 or 1 checks are copied unchanged. Non-Python tests are copied
unchanged. Output mirrors the input layout under ``testgen_combined_splitted/``
and the per-entry ``test_code`` inside each ``result.json`` is rewritten to the
split source so the existing validator picks it up directly.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import logging
import shutil
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("split_tests")


# --- assertion detection -------------------------------------------------- #

def _is_assert_call(node: ast.AST) -> bool:
    """True for assertion-style *calls*: self.assertX, *.fail, np.testing.assert_*."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        attr = func.attr
        if attr.startswith("assert") or attr in {"fail", "failUnless", "failIf"}:
            return True
    return False


def _is_raises_with(node: ast.AST) -> bool:
    """True for ``with pytest.raises(...)`` / ``with self.assertRaises(...)`` items."""
    if not isinstance(node, (ast.With, ast.AsyncWith)):
        return False
    for item in node.items:
        call = item.context_expr
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute):
            if call.func.attr in {"raises", "assertRaises", "assertRaisesRegex", "warns"}:
                return True
    return False


def contains_assertion(node: ast.AST) -> bool:
    """Does this statement contain any assertion-like construct (nested included)?"""
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if _is_assert_call(child):
            return True
        if _is_raises_with(child):
            return True
    return False


# --- name binding / use analysis (for the safety guard) ------------------- #

def assigned_names(node: ast.AST) -> set[str]:
    """Names *bound* anywhere within ``node`` (for the dropped-binding guard)."""
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
            names.add(child.id)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(child.name)
        elif isinstance(child, ast.alias):
            names.add((child.asname or child.name).split(".")[0])
        elif isinstance(child, ast.ExceptHandler) and child.name:
            names.add(child.name)
    return names


def used_names(node: ast.AST) -> set[str]:
    """Names *read* (Load context) anywhere within ``node``."""
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
    }


_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def has_escaping_control_flow(stmt: ast.AST) -> bool:
    """True if ``stmt`` contains return/raise/break/continue at the test's own
    control-flow level (i.e. not buried inside a nested def/lambda).

    Such statements form *guards*: an early ``return`` / ``raise`` can prevent
    later statements from running, so a check that holds one cannot be dropped
    from a sibling sub-test without changing behaviour. We therefore refuse to
    split functions that contain any.
    """
    found = False

    def walk(node: ast.AST) -> None:
        nonlocal found
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                found = True
                return
            if isinstance(child, _NESTED_SCOPES):
                continue  # deferred scope: its control flow does not escape
            walk(child)

    walk(stmt)
    return found


def is_pure_assert_check(stmt: ast.AST) -> bool:
    """True if ``stmt`` verifies *only* via bare ``assert`` statements.

    A check is unsafe to drop when it can drive state that later checks read --
    typically a ``with pytest.raises(...)`` / ``self.assertRaises`` block or a
    ``self.assert*`` call wrapping code execution, or a ``with``/``try`` block
    whose body has side effects. We only split when every check is expressed as
    a plain ``assert`` (optionally nested inside ``if``/``for``/``while``).
    """
    if isinstance(stmt, (ast.With, ast.AsyncWith, ast.Try)):
        return False
    for node in ast.walk(stmt):
        if _is_raises_with(node) or _is_assert_call(node):
            return False
    return True


# --- the core split ------------------------------------------------------- #

def split_function(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    """Return either [func] (unchanged) or a list of per-check sub-functions."""
    body = func.body
    check_indices = [i for i, stmt in enumerate(body) if contains_assertion(stmt)]

    # Nothing to gain from splitting a single (or zero) check.
    if len(check_indices) <= 1:
        return [func]

    check_set = set(check_indices)

    # Safety guard A: escaping control flow (early return/raise/break/continue)
    # anywhere in the function makes statement order significant -> keep whole.
    if any(has_escaping_control_flow(stmt) for stmt in body):
        logger.debug("  keep whole (escaping control flow) in %s", func.name)
        return [func]

    # Safety guard B: every check must verify via bare ``assert`` only. A
    # ``with pytest.raises``/``assertRaises``/``self.assert*`` check can drive
    # side effects that later checks depend on -> keep whole.
    if not all(is_pure_assert_check(body[c]) for c in check_indices):
        logger.debug("  keep whole (non-pure-assert check) in %s", func.name)
        return [func]

    # Safety guard C: a check that binds a name used by any *later* statement
    # cannot be dropped without breaking that later statement -> refuse split.
    for c in check_indices:
        bound = assigned_names(body[c])
        if not bound:
            continue
        for later in body[c + 1:]:
            if bound & used_names(later):
                logger.debug(
                    "  keep whole (check binds %s used later) in %s",
                    bound & used_names(later),
                    func.name,
                )
                return [func]

    # Build one sub-function per check: preceding *setup* statements + the check.
    new_funcs: list[ast.stmt] = []
    for n, j in enumerate(check_indices, start=1):
        prefix = [body[k] for k in range(j) if k not in check_set]
        sub_body = [copy.deepcopy(s) for s in prefix] + [copy.deepcopy(body[j])]

        sub = copy.deepcopy(func)
        sub.name = f"{func.name}__a{n}"
        sub.body = sub_body
        new_funcs.append(sub)

    return new_funcs


def split_module_source(source: str) -> tuple[str, dict]:
    """Split every module-level ``def test_*`` in ``source``.

    Returns (new_source, stats). On any parse error the original source is
    returned unchanged with ``stats['parse_error']`` set.
    """
    stats = {"functions": 0, "split_functions": 0, "checks": 0, "kept_whole": 0}
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return source, {"parse_error": str(exc), **stats}

    new_body: list[ast.stmt] = []
    changed = False
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test")
        ):
            stats["functions"] += 1
            replacements = split_function(node)
            if len(replacements) > 1:
                stats["split_functions"] += 1
                stats["checks"] += len(replacements)
                changed = True
            else:
                stats["kept_whole"] += 1
            new_body.extend(replacements)
        else:
            new_body.append(node)

    if not changed:
        return source, stats

    tree.body = new_body
    ast.fix_missing_locations(tree)
    header = (
        "# AUTO-GENERATED by split_acceptance_tests.py\n"
        "# Each original test function was split into one function per top-level\n"
        "# assertion so pytest reports per-check pass/fail counts.\n"
    )
    return header + ast.unparse(tree) + "\n", stats


# --- driver --------------------------------------------------------------- #

def process_instance_dir(src_dir: Path, dst_dir: Path) -> dict:
    """Split all python tests in one instance dir; rewrite result.json test_code."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    agg = {"py_files": 0, "split_files": 0, "parse_errors": 0, "total_checks": 0}

    result_path = src_dir / "result.json"
    result = None
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))

    # Map test_file basename -> split source, so result.json can be rewritten.
    split_by_basename: dict[str, str] = {}

    for py in sorted(src_dir.glob("*.py")):
        agg["py_files"] += 1
        source = py.read_text(encoding="utf-8")
        new_source, stats = split_module_source(source)
        if stats.get("parse_error"):
            agg["parse_errors"] += 1
            logger.warning("  parse error in %s: %s", py, stats["parse_error"])
        if new_source != source:
            agg["split_files"] += 1
            agg["total_checks"] += stats.get("checks", 0)
        (dst_dir / py.name).write_text(new_source, encoding="utf-8")
        split_by_basename[py.name] = new_source

    # Rewrite result.json: replace python entries' test_code with split source.
    if result is not None:
        for entry in result.get("results", []):
            if entry.get("language") != "python":
                continue
            test_file = entry.get("test_file", "")
            basename = Path(test_file).name
            if basename in split_by_basename:
                entry["test_code"] = split_by_basename[basename]
        (dst_dir / "result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )

    # Copy any other non-.py / non-result.json artifacts verbatim.
    for extra in src_dir.iterdir():
        if extra.suffix == ".py" or extra.name == "result.json":
            continue
        if extra.is_file():
            shutil.copy2(extra, dst_dir / extra.name)

    return agg


def main() -> None:
    parser = argparse.ArgumentParser(description="Split acceptance tests per assertion")
    parser.add_argument("--src", default="testgen_combined")
    parser.add_argument("--dst", default="testgen_combined_splitted")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    src_root = Path(args.src)
    dst_root = Path(args.dst)
    dst_root.mkdir(parents=True, exist_ok=True)

    instance_dirs = sorted(d for d in src_root.iterdir() if d.is_dir())
    if args.limit:
        instance_dirs = instance_dirs[: args.limit]

    totals = {"instances": 0, "py_files": 0, "split_files": 0, "parse_errors": 0, "total_checks": 0}
    for d in instance_dirs:
        agg = process_instance_dir(d, dst_root / d.name)
        totals["instances"] += 1
        for k in ("py_files", "split_files", "parse_errors", "total_checks"):
            totals[k] += agg[k]

    logger.info(
        "Done: %d instances, %d py files, %d files split into %d checks, %d parse errors -> %s",
        totals["instances"],
        totals["py_files"],
        totals["split_files"],
        totals["total_checks"],
        totals["parse_errors"],
        dst_root,
    )


if __name__ == "__main__":
    main()
