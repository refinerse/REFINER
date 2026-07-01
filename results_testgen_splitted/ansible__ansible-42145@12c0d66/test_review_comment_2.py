import re


SOURCE_PATH = "/workspace/lib/ansible/modules/network/meraki/meraki_config_template.py"


def _get_func_body(source: str, func_name: str) -> str:
    # Extract function body text (not AST) by locating from "def name(" to the next top-level "def " or EOF.
    m = re.search(rf"^def\s+{re.escape(func_name)}\s*\(.*?\):\s*$", source, flags=re.M)
    assert m, f"Expected to find function definition for {func_name}() in {SOURCE_PATH}"
    start = m.end()
    m2 = re.search(r"^def\s+\w+\s*\(.*?\):\s*$", source[start:], flags=re.M)
    end = start + (m2.start() if m2 else len(source) - start)
    return source[start:end]


def test_meraki_template_helpers_use_guard_clause_no_else_on_success_path():
    """
    Review wants the 'default flow' to return response and error cases handled in an if-block:
        if meraki.status != 200: meraki.fail_json(...)
        return response

    The 'before' version used:
        if meraki.status == 200: return response
        else: meraki.fail_json(...)
    which is explicitly unwanted.
    """
    source = open(SOURCE_PATH, "r", encoding="utf-8").read()

    # Functions discussed in the diff.
    checks = [
        ("get_config_templates", "return response", "Unable to get configuration templates"),
        ("delete_template", "return response", "Unable to remove configuration template"),
        ("bind", "return r", "Unable to bind configuration template to network"),
        ("unbind", "return r", "Unable to unbind configuration template from network"),
    ]

    for func_name, return_stmt, fail_msg in checks:
        body = _get_func_body(source, func_name)

        assert "else:" not in body, (
            f"{func_name}() should not use an 'else:' block; it should use a guard-clause "
            f"(if status != 200: fail_json) and then fall through to {return_stmt}."
        )

        # Require the guard-clause form explicitly to ensure we fail on the "before" code.
        assert re.search(r"if\s+meraki\.status\s*!=\s*200\s*:", body), (
            f"{func_name}() should guard error cases with `if meraki.status != 200:`."
        )
        assert fail_msg in body, (
            f"{func_name}() should call fail_json with message containing: {fail_msg!r}."
        )
        assert return_stmt in body, (
            f"{func_name}() should have the success-path as the default flow ({return_stmt})."
        )