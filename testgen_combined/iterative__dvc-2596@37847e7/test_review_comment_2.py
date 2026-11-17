import re


def test_bash_completion_no_early_return_if_arg_starts_with_dash():
    source = open("/workspace/scripts/completion/dvc.bash", encoding="utf-8").read()

    # The review comment requests removing the if-block that returned early when
    # the command word starts with "-", since the hyphen->underscore replacement
    # will resolve to an empty variable and "simply work".
    #
    # Before: had blocks like:
    #   if [[ ${COMP_WORDS[1]:0:1} == "-" ]]; then
    #     return 0
    #   else
    #     local options_list=...
    #     COMPREPLY=...
    #   fi
    #
    # After: no such early-return blocks; always computes options_list and COMPREPLY.

    assert "return 0" in source, "Sanity check: expected bash completion function to contain 'return 0'."

    # Ensure there are no early-return guards for COMP_WORDS[1] or COMP_WORDS[2] starting with '-'.
    # This is the structural change under review.
    forbidden_patterns = [
        r"if\s+\[\[\s*\$\{COMP_WORDS\[1\]:0:1\}\s*==\s*\"-\"\s*\]\]\s*;\s*then\s*[\s\S]*?\breturn\s+0\b",
        r"if\s+\[\[\s*\$\{COMP_WORDS\[2\]:0:1\}\s*==\s*\"-\"\s*\]\]\s*;\s*then\s*[\s\S]*?\breturn\s+0\b",
    ]
    for pat in forbidden_patterns:
        assert not re.search(
            pat, source
        ), (
            "Bash completion script should not early-return when a command/subcommand begins with '-' "
            "(the hyphen->underscore replacement should handle it by expanding an empty variable). "
            "Found an if-guard with 'return 0' that should have been removed."
        )