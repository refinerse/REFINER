#!/usr/bin/env python3
"""Classify generated validation tests as structural or behavioural.

  structural  - the test only inspects code: reads source files, greps text,
                parses ASTs, or passes imported objects to source-introspection
                helpers (inspect.getsource, hasattr, ...). Nothing from the
                project is executed.
  behavioural - the test imports a non-stdlib module (the project or a library)
                and uses it at runtime: calls functions, instantiates classes,
                reads runtime values, or runs code via subprocess/runpy/exec.

Python tests are classified from their AST. JS/TS tests use a regex heuristic:
behavioural iff they require/import a non-builtin module.

Usage:
  python classify_validation_tests.py
  python classify_validation_tests.py agents_results/results_testgen_qwen_3.6_plus \
      --output-csv validation_test_types.csv
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
import warnings
from collections import Counter
from pathlib import Path

DEFAULT_TESTGEN_DIRS = [
    Path("agents_results/results_testgen_qwen_3.6_plus"),
    Path("agents_results/results_testgen_qwen_3.6_flash"),
    Path("agents_results/results_testgen_claude_sonnet_4.6"),
]
DEFAULT_OUTPUT_CSV = Path("validation_test_types.csv")

STRUCTURAL = "structural"
BEHAVIOURAL = "behavioural"

# Test-infrastructure modules: importing these does not exercise the project.
TEST_LIBS = {"pytest", "_pytest", "unittest", "mock", "hypothesis"}
# Calls that only look at an object's code/shape without running it.
INTROSPECTION_CALLS = {
    "inspect.getsource", "inspect.getsourcelines", "inspect.getsourcefile",
    "inspect.getfile", "inspect.getmodule", "inspect.getdoc", "inspect.getcomments",
    "inspect.signature", "inspect.isfunction", "inspect.isclass", "inspect.ismethod",
    "hasattr", "dir", "callable", "type", "id",
}
# Calls that execute code even without a project import.
EXEC_CALLS = {
    "subprocess.run", "subprocess.call", "subprocess.check_call", "subprocess.check_output",
    "subprocess.Popen", "os.system", "os.popen", "runpy.run_path", "runpy.run_module",
    "exec", "eval",
}
# Calls that import a module dynamically and return it.
DYNAMIC_IMPORT_CALLS = {"importlib.import_module", "__import__", "pytest.importorskip"}

NODE_BUILTINS = {
    "fs", "path", "os", "util", "assert", "child_process", "url", "crypto",
    "node:fs", "node:path", "node:assert", "node:child_process",
}
JS_IMPORT_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)|^\s*import\s[^'"]*['"]([^'"]+)['"]""", re.M)


def is_external_module(name: str) -> bool:
    top = name.split(".")[0]
    return bool(top) and top not in sys.stdlib_module_names and top not in TEST_LIBS


def dotted(node: ast.AST) -> str | None:
    """'a.b.c' for a Name/Attribute chain, else None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def root_name(node: ast.AST) -> str | None:
    """Base Name of an attribute/call/subscript chain (`a` in `a.b().c[0]`)."""
    while isinstance(node, (ast.Attribute, ast.Call, ast.Subscript)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


def classify_python(source: str) -> tuple[str, str]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except SyntaxError as exc:
        return BEHAVIOURAL if re.search(r"^\s*(from|import)\s", source, re.M) else STRUCTURAL, f"unparseable: {exc.msg}"

    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    # Names bound to external (non-stdlib, non-test) modules or objects from them.
    external: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            external.update((a.asname or a.name.split(".")[0]) for a in node.names if is_external_module(a.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level or is_external_module(node.module or ""):
                external.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and dotted(node.value.func) in DYNAMIC_IMPORT_CALLS:
            external.update(t.id for t in node.targets if isinstance(t, ast.Name))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and dotted(node.func) in EXEC_CALLS:
            return BEHAVIOURAL, f"executes code via {dotted(node.func)}"

    # Every load of an external name must sit inside an introspection call to stay structural.
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Name) and node.id in external and isinstance(node.ctx, ast.Load)):
            continue
        cur = node
        while cur in parents:
            parent = parents[cur]
            if isinstance(parent, ast.Call) and cur is not parent.func and dotted(parent.func) in INTROSPECTION_CALLS:
                break
            if isinstance(parent, (ast.stmt, ast.Lambda)):
                return BEHAVIOURAL, f"uses imported '{node.id}' at runtime (line {node.lineno})"
            cur = parent

    if external:
        return STRUCTURAL, f"imports {sorted(external)} only for source introspection"
    return STRUCTURAL, "no external import; inspects source text"


def classify_js(source: str) -> tuple[str, str]:
    modules = [a or b for a, b in JS_IMPORT_RE.findall(source)]
    # ponytail: import-only check, a JS test that imports a module but only reads files would be mislabelled; add call analysis if JS tests grow beyond a handful.
    external = [m for m in modules if m not in NODE_BUILTINS and not m.startswith("@jest/")]
    if external:
        return BEHAVIOURAL, f"imports {external}"
    return STRUCTURAL, "only builtin modules; inspects source text"


def classify_file(path: Path) -> tuple[str, str]:
    source = path.read_text(errors="replace")
    return classify_python(source) if path.suffix == ".py" else classify_js(source)


def iter_tests(testgen_dir: Path):
    """Yield (instance_id, comment_result, test_path) for every generated test."""
    for result_file in sorted(testgen_dir.glob("*/result.json")):
        data = json.loads(result_file.read_text())
        for comment in data.get("results", []):
            test_file = comment.get("test_file")
            if test_file:
                yield data.get("instance_id", result_file.parent.name), comment, testgen_dir / test_file


def self_check() -> None:
    assert classify_python("def test():\n    assert 'x' in open('/workspace/a.py').read()")[0] == STRUCTURAL
    assert classify_python("import inspect, pkg\ndef test():\n    assert 'x' in inspect.getsource(pkg.f)")[0] == STRUCTURAL
    assert classify_python("from pkg import C\ndef test():\n    assert hasattr(C, 'm')")[0] == STRUCTURAL
    assert classify_python("from pkg import f\ndef test():\n    assert f(1) == 2")[0] == BEHAVIOURAL
    assert classify_python("import pkg\ndef test():\n    assert pkg.CONST == 3")[0] == BEHAVIOURAL
    assert classify_python("import subprocess\ndef test():\n    subprocess.run(['python', '-c', '1'])")[0] == BEHAVIOURAL
    assert classify_js("const fs = require('fs'); fs.readFileSync('/workspace/a.js')")[0] == STRUCTURAL
    assert classify_js("const P = require('/workspace/js/p.js');")[0] == BEHAVIOURAL
    print("self-check ok")


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify generated validation tests as structural or behavioural.")
    parser.add_argument("testgen_dirs", nargs="*", type=Path, default=DEFAULT_TESTGEN_DIRS)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--self-check", action="store_true", help="Run the built-in classifier checks and exit")
    args = parser.parse_args()
    if args.self_check:
        return self_check()

    rows = []
    for testgen_dir in args.testgen_dirs:
        for instance_id, comment, test_path in iter_tests(testgen_dir):
            if not test_path.exists():
                print(f"missing test file: {test_path}", file=sys.stderr)
                continue
            category, reason = classify_file(test_path)
            assessment = comment.get("assessment") or {}
            rows.append({
                "backbone": testgen_dir.name,
                "instance_id": instance_id,
                "comment_index": comment.get("comment_index"),
                "test_file": str(test_path),
                "category": category,
                "reason": reason,
                "expected_failure_observed": comment.get("expected_failure_observed"),
                "gt_patch_passed": assessment.get("ground_truth_patch_passed"),
            })

    with args.output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter((r["backbone"], r["category"]) for r in rows)
    gt_pass = Counter((r["backbone"], r["category"]) for r in rows if r["gt_patch_passed"] is True)
    print(f"{'backbone':36} {'category':12} {'tests':>6} {'share':>7} {'GT-patch pass':>14}")
    for backbone in dict.fromkeys(r["backbone"] for r in rows):
        total = sum(counts[(backbone, c)] for c in (STRUCTURAL, BEHAVIOURAL))
        for category in (STRUCTURAL, BEHAVIOURAL):
            n = counts[(backbone, category)]
            passed = gt_pass[(backbone, category)]
            print(f"{backbone:36} {category:12} {n:6} {n / total:7.1%} {passed:6}/{n:<4} {passed / n if n else 0:5.1%}")
    print(f"\nwrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
