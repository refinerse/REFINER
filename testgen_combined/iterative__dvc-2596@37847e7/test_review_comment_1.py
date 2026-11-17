import re


def test_bash_completion_replaces_hyphen_in_comp_words_1_and_2():
    source = open("/workspace/scripts/completion/dvc.bash", encoding="utf-8").read()

    # The bug: using COMP_WORDS[1] verbatim when building options_list can
    # yield invalid variable names like `_dvc_import-url`, breaking completion.
    # Fix: wrap COMP_WORDS[1] in replace_hyphen(...) anywhere it is used to
    # build the `_dvc_...` variable name (both COMP_CWORD==2 and ==3 branches).

    # 1) In COMP_CWORD==2 branch: must be `_dvc_$(replace_hyphen ${COMP_WORDS[1]})`
    assert re.search(
        r'options_list="_dvc_\$\(\s*replace_hyphen\s+\$\{COMP_WORDS\[1\]\}\s*\)"',
        source,
    ), (
        "Bash completion should replace hyphens in COMP_WORDS[1] when building "
        'options_list for COMP_CWORD==2, e.g. options_list="_dvc_$(replace_hyphen ${COMP_WORDS[1]})". '
        "Without this, commands like 'import-url'/'get-url' produce invalid variable names."
    )

    # 2) In COMP_CWORD==3 branch: must also replace hyphens in COMP_WORDS[1]
    # (and COMP_WORDS[2]) when building nested option list names.
    assert re.search(
        r'options_list="_dvc_\$\(\s*replace_hyphen\s+\$\{COMP_WORDS\[1\]\}\s*\)_\$\(\s*replace_hyphen\s+\$\{COMP_WORDS\[2\]\}\s*\)"',
        source,
    ), (
        "Bash completion should replace hyphens in BOTH COMP_WORDS[1] and COMP_WORDS[2] "
        'when building options_list for COMP_CWORD==3, e.g. options_list="_dvc_$(replace_hyphen ${COMP_WORDS[1]})_$(replace_hyphen ${COMP_WORDS[2]})". '
        "Using COMP_WORDS[1] unmodified breaks completion for hyphenated commands."
    )