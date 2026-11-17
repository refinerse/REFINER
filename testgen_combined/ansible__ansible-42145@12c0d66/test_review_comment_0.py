import re

SOURCE_PATH = "/workspace/lib/ansible/modules/network/meraki/meraki_config_template.py"


def test_no_unneeded_else_after_status_check():
    source = open(SOURCE_PATH, "r", encoding="utf-8").read()

    # The review requested removing the "else" branch after returning on success.
    # Before:   if meraki.status == 200: return ... else: meraki.fail_json(...)
    # After:    if meraki.status != 200: meraki.fail_json(...); return ...
    #
    # Enforce the new pattern: there must be NO "if meraki.status == 200:" blocks
    # that also contain an "else:" (unneeded/unwanted).
    bad_pattern = re.compile(
        r"if\s+meraki\.status\s*==\s*200\s*:\s*\n"
        r"(?:[ \t]+\S.*\n)*?"
        r"[ \t]*else\s*:\s*\n",
        re.MULTILINE,
    )

    assert not bad_pattern.search(source), (
        "Found an 'else:' following 'if meraki.status == 200:'; "
        "the else is unneeded/unwanted per review. Expected pattern is "
        "'if meraki.status != 200: meraki.fail_json(...); return ...' without an else."
    )

    # Additionally ensure the preferred inversion exists at least once in this module,
    # proving the refactor was applied (and making this test reliably fail on 'before').
    assert "if meraki.status != 200:" in source, (
        "Expected status checks to be inverted to 'if meraki.status != 200:' "
        "with fail_json, avoiding an else branch."
    )