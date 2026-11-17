import re


SOURCE_PATH = "/workspace/lib/ansible/modules/network/meraki/meraki_config_template.py"


def _get_func_block(source: str, func_name: str) -> str:
    # Grab from "def func_name(" up to the next top-level "def " or EOF.
    m = re.search(rf"^def {re.escape(func_name)}\s*\(.*?\):\n", source, flags=re.M)
    assert m, f"Expected to find function definition for {func_name} in {SOURCE_PATH}"
    start = m.start()
    m2 = re.search(r"^def \w+\s*\(.*?\):\n", source[m.end():], flags=re.M)
    end = (m.end() + m2.start()) if m2 else len(source)
    return source[start:end]


def test_no_redundant_else_after_status_check_in_meraki_config_template():
    """
    Review requires removing the redundant 'else' after a branch that returns.
    We enforce the post-fix pattern:
      if meraki.status != 200: fail_json(...)
      return <response>
    and disallow the pre-fix pattern:
      if meraki.status == 200: return <response>
      else: fail_json(...)
    """
    source = open(SOURCE_PATH, "r", encoding="utf-8").read()

    # Functions touched by the change where the redundant else existed.
    funcs = ["get_config_templates", "delete_template", "bind", "unbind"]

    for fn in funcs:
        block = _get_func_block(source, fn)

        assert "if meraki.status != 200" in block, (
            f"{fn} should use a guard clause 'if meraki.status != 200: meraki.fail_json(...)' "
            f"instead of returning in the if-branch."
        )

        assert "if meraki.status == 200" not in block, (
            f"{fn} should not have 'if meraki.status == 200: return ...' since it encourages an "
            f"unneeded 'else:' block; use 'if meraki.status != 200: fail_json' then return."
        )

        # Specifically ensure the unwanted else pattern isn't present.
        assert not re.search(r"if\s+meraki\.status\s*==\s*200\s*:\s*\n\s*return\b.*\n\s*else\s*:", block), (
            f"{fn} still appears to use 'if status == 200: return ... else:' which the review "
            f"comment asked to remove."
        )