import re


def test_deploy_remote_cluster_askpass_block_is_deduplicated():
    source = open(
        "/workspace/sky/utils/kubernetes/deploy_remote_cluster.sh", "r", encoding="utf-8"
    ).read()

    # After the review: the repeated askpass snippet is factored into a reusable
    # ASKPASS_BLOCK string and injected via "$ASKPASS_BLOCK" in each run_remote heredoc.
    # Before: the snippet is inlined multiple times and ASKPASS_BLOCK does not exist.

    assert "ASKPASS_BLOCK=" in source, (
        "Expected a factored-out ASKPASS_BLOCK variable to exist to avoid repeating "
        "the sudo askpass setup snippet, but no 'ASKPASS_BLOCK=' definition was found."
    )

    # In the fixed version, the file still contains the comment once in the block
    # and may contain an additional comment near the definition (e.g., explaining it).
    # We only want to ensure the large inline snippet is not duplicated across
    # multiple run_remote blocks.
    inline_marker = "# Create temporary askpass script"
    occurrences = [m.start() for m in re.finditer(re.escape(inline_marker), source)]
    assert len(occurrences) <= 2, (
        "Expected the askpass setup text to be centralized (at most in the ASKPASS_BLOCK "
        "definition plus possibly one explanatory comment), but found "
        f"{len(occurrences)} occurrences of '{inline_marker}', suggesting it is still "
        "inlined repeatedly."
    )

    # The key behavioral change: multiple remote command blocks should include $ASKPASS_BLOCK
    # instead of copying the whole snippet.
    uses = len(re.findall(r"^\s*\$ASKPASS_BLOCK\s*$", source, flags=re.MULTILINE))
    assert uses >= 4, (
        "Expected $ASKPASS_BLOCK to be reused in several run_remote command blocks "
        "(cleanup server, cleanup agent, head install, worker install, gpu operator), "
        f"but found only {uses} standalone uses."
    )

    # Ensure the old inlined form isn't present (it used to echo \"$PASSWORD\" in multiple places).
    # In the refactor, password is referenced inside the block as `echo $PASSWORD` (unquoted),
    # and should not appear as repeated `echo "$PASSWORD"` lines.
    assert source.count('echo "$PASSWORD"') == 0, (
        "Expected the old inlined askpass script form `echo \"$PASSWORD\"` to be removed "
        "after factoring into ASKPASS_BLOCK, but it is still present."
    )