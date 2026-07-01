import re


def _extract_step_block(workflow: str, step_name: str) -> str:
    """
    Extract the YAML text block for a given GitHub Actions step name.
    This is indentation-based and avoids needing a YAML parser.
    """
    lines = workflow.splitlines(True)

    # Locate the step header: "- name: <step_name>"
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^\s*-\s*name:\s*{re.escape(step_name)}\s*$", line):
            start = i
            break
    assert start is not None, f"Expected to find a step named '{step_name}'."

    # Determine the indentation of the "- name:" line, and capture until next step at same indent.
    step_indent = len(re.match(r"^(\s*)", lines[start]).group(1))
    out = [lines[start]]

    for j in range(start + 1, len(lines)):
        line = lines[j]
        # A new step begins with "- " at the same indentation level.
        if re.match(rf"^\s{{{step_indent}}}-\s+", line):
            break
        out.append(line)

    return "".join(out)


def test_lint_workflow_mypy_reports_errors_not_warnings():
    path = "/workspace/.github/workflows/lint.yml"
    source = open(path, "r", encoding="utf-8").read()

    step_block = _extract_step_block(source, "Run mypy")

    assert re.search(r"(?m)^\s*level:\s*error\s*$", step_block), (
        "Expected the 'Run mypy' GitHub Actions step to set `level: error` so that "
        "mypy findings are treated as errors (not warnings)."
    )