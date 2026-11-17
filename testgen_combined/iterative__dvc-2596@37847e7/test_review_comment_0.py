import re


def test_no_early_return_option_guard_blocks_in_completion_script():
    """
    The review comment indicates the `if` blocks that early-return when the
    previous word starts with '-' are unnecessary and should be removed.

    Verify the bash completion script does NOT contain these early-return guards.
    This fails on the "before" version (guards present) and passes on "after"
    (guards removed).
    """
    source = open("/workspace/scripts/completion/dvc.bash", "r", encoding="utf-8").read()

    # Patterns representing the unnecessary guard blocks added in the "before" code.
    # We check specifically for the early-return behavior tied to COMP_WORDS[1]/[2].
    guard_cword2 = re.compile(
        r'elif\s+\[\s*"\$\{COMP_CWORD\}"\s+-eq\s+2\s*\]\s*;\s+then'
        r".*?\[\[\s*\$\{COMP_WORDS\[1\]:0:1\}\s*==\s*\"-\"\s*\]\]\s*;"
        r"\s*then\s*return\s+0",
        re.DOTALL,
    )
    guard_cword3 = re.compile(
        r'elif\s+\[\s*"\$\{COMP_CWORD\}"\s+-eq\s+3\s*\]\s*;\s+then'
        r".*?\[\[\s*\$\{COMP_WORDS\[2\]:0:1\}\s*==\s*\"-\"\s*\]\]\s*;"
        r"\s*then\s*return\s+0",
        re.DOTALL,
    )

    assert not guard_cword2.search(source), (
        "Bash completion script should not early-return for COMP_CWORD==2 when "
        "COMP_WORDS[1] starts with '-'; the unnecessary guard if-block should be removed."
    )
    assert not guard_cword3.search(source), (
        "Bash completion script should not early-return for COMP_CWORD==3 when "
        "COMP_WORDS[2] starts with '-'; the unnecessary guard if-block should be removed."
    )