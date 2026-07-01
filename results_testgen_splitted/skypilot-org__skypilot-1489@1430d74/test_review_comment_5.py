import os
import re


def test_config_v2_removed_or_deprecated_after_flag_merge():
    """After the refactor discussed in the review, config_v2.py should no longer
    exist (changes merged back behind a feature flag in config.py), or at most be
    a tiny shim. Before the change, config_v2.py exists and is a large file.
    """
    path = "/workspace/sky/skylet/providers/aws/config_v2.py"

    if not os.path.exists(path):
        # After version: file removed -> PASS.
        assert True
        return

    # If the file still exists, it must be a small shim (not a full duplicate).
    source = open(path, "r", encoding="utf-8").read()
    line_count = source.count("\n") + 1
    def_count = len(re.findall(r"(?m)^\s*def\s+\w+\s*\(", source))

    assert (
        line_count < 200 and def_count < 5
    ), (
        "Expected config_v2.py to be removed (preferred) or converted into a small "
        "shim after merging changes back into the original config.py with a feature "
        "flag. Found a large implementation instead "
        f"(lines={line_count}, defs={def_count})."
    )