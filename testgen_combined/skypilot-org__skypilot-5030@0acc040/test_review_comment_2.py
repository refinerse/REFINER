import re


def test_askpass_block_is_factored_out_and_reused():
    source = open("/workspace/sky/utils/kubernetes/deploy_remote_cluster.sh").read()

    # Must define a reusable block/macro.
    assert "ASKPASS_BLOCK=" in source, (
        "Expected deploy_remote_cluster.sh to define a reusable ASKPASS_BLOCK "
        "macro/string for the repeated sudo-askpass snippet."
    )

    # The askpass snippet header should not be copy-pasted at call sites.
    # In the refactor, it appears inside ASKPASS_BLOCK and may also appear once
    # in the leading comment above ASKPASS_BLOCK (so allow up to 2 total).
    occurrences = source.count("# Create temporary askpass script")
    assert occurrences <= 2, (
        "Expected the repeated askpass snippet to be factored into ASKPASS_BLOCK "
        "and not duplicated at each run_remote site. "
        f"Found {occurrences} occurrences of '# Create temporary askpass script'."
    )

    # Reuse should be visible at multiple remote execution sites.
    uses = len(re.findall(r"^\s*\$ASKPASS_BLOCK\s*$", source, flags=re.MULTILINE))
    assert uses >= 3, (
        "Expected '$ASKPASS_BLOCK' to be reused at multiple remote execution sites "
        f"(cleanup/install/gpu steps). Found {uses} standalone uses."
    )

    # mktemp creation should be present (in ASKPASS_BLOCK); in the "before" version
    # it was duplicated at each remote command site (many occurrences).
    # Match both escaped and unescaped forms.
    mktemp_occ = len(
        re.findall(r"ASKPASS_SCRIPT=\\?\$\(\s*mktemp\s*\)", source)
    )
    assert mktemp_occ <= 2, (
        "Expected the askpass mktemp creation to be defined once via ASKPASS_BLOCK "
        "(optionally plus one extra occurrence in comments/formatting), not repeated "
        f"across the file. Found {mktemp_occ} occurrences matching "
        "'ASKPASS_SCRIPT=$(mktemp)' (including escaped forms)."
    )