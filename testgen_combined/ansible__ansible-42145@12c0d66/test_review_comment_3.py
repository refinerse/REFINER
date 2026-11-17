import re


def test_no_unneeded_else_after_status_check_in_meraki_config_template():
    source = open("/workspace/lib/ansible/modules/network/meraki/meraki_config_template.py", "r", encoding="utf-8").read()

    # The review comment requests removing the "else" after:
    #   if meraki.status == 200: return ...
    # The addressed version inverts the condition:
    #   if meraki.status != 200: fail_json(...)
    #   return ...
    #
    # This test enforces that there are no occurrences of the unwanted pattern
    # "if meraki.status == 200: ... return ... else:" in this module.
    unwanted = re.compile(
        r"if\s+meraki\.status\s*==\s*200\s*:\s*\n"
        r"(?:[ \t].*\n)*?"
        r"[ \t]*return\b.*\n"
        r"[ \t]*else\s*:\s*\n",
        re.MULTILINE,
    )

    matches = list(unwanted.finditer(source))
    assert not matches, (
        "Found an unnecessary 'else:' after a successful status check "
        "(pattern: `if meraki.status == 200: ... return ... else:`). "
        "The reviewed change requires removing this else (e.g., invert the check and early-fail)."
    )

    # Also ensure the preferred style exists at least once so the test is tied to the intended change.
    assert "if meraki.status != 200:" in source, (
        "Expected the module to use inverted status checks (`if meraki.status != 200: fail_json(...)`) "
        "instead of `if meraki.status == 200: return ... else: ...`."
    )