import re


def test_L009_fixture_uses_quoted_string_for_templated_newlines():
    """The L009 YAML fixture should represent the templated newlines as a quoted string,
    not a YAML multiline block scalar, to avoid ambiguity about preserved trailing newlines.
    """
    path = "/workspace/test/fixtures/rules/std_rule_cases/L009.yml"
    source = open(path, encoding="utf-8").read()

    # The updated fixture should include the quoted equivalent.
    assert (
        "test_pass_templated_plus_raw_newlines:\n  pass_str: \"{{ '\\n\\n' }}\\n\"\n"
        in source
    ), (
        "Expected L009.yml to define test_pass_templated_plus_raw_newlines.pass_str as the "
        'quoted string "{{ \'\\n\\n\' }}\\n", not a YAML multiline block. '
        f"File: {path}"
    )

    # And it should no longer use a YAML multiline block for this case.
    assert not re.search(
        r"test_pass_templated_plus_raw_newlines:\n\s+pass_str:\s*\|\n", source
    ), (
        "Expected L009.yml not to use a YAML multiline block scalar (pass_str: |) for "
        "test_pass_templated_plus_raw_newlines. The review requested switching to a quoted "
        "string to make the trailing newline explicit."
    )