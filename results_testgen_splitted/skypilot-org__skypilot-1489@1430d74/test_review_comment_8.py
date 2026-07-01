import os
import re


def test_configure_iam_role_does_not_use_undefined_profile_var():
    # The module isn't importable in this environment; use source inspection.
    # The fix may have been applied in config_v2.py or config.py depending on refactor.
    candidates = [
        "/workspace/sky/skylet/providers/aws/config_v2.py",
        "/workspace/sky/skylet/providers/aws/config.py",
    ]
    source_path = next((p for p in candidates if os.path.exists(p)), None)
    assert source_path is not None, (
        "Expected to find AWS config source file in repo under one of: "
        f"{candidates}. None exist."
    )

    source = open(source_path, "r", encoding="utf-8").read()

    # Extract the _configure_iam_role function body (if present).
    # The "after" version may have moved/removed this function; in that case,
    # the specific bug ('profile' undefined) cannot exist in the same way.
    m = re.search(
        r"\n(?:async\s+)?def\s+_configure_iam_role\s*\([^)]*\)\s*:(?P<body>.*?)(?=\n\ndef\s|\n\nasync\s+def\s|\Z)",
        source,
        flags=re.S,
    )
    if m is None:
        # After refactor: function doesn't exist in this file, which implies
        # the exact buggy pattern can't be present here. Still assert the
        # buggy snippet is absent.
        assert "profile.arn" not in source, (
            "Found `profile.arn` in AWS config source, which indicates the old bug "
            "(using an undefined `profile` variable) may still be present."
        )
        return

    func_body = m.group("body")

    # Find the specific branch mentioned in the review:
    # if "IamInstanceProfile" in head_node_config:
    b = re.search(
        r'if\s+["\']IamInstanceProfile["\']\s+in\s+head_node_config\s*:(?P<branch>.*?)(?=\n\s*(elif|else)\b|\n\s*return\b|\Z)',
        func_body,
        flags=re.S,
    )
    assert b is not None, (
        "Expected `_configure_iam_role` to contain the branch "
        '`if "IamInstanceProfile" in head_node_config:`.'
    )
    branch = b.group("branch")

    # Core regression check:
    # Before code incorrectly used `profile.arn` in this branch (profile undefined).
    assert "profile.arn" not in branch, (
        "Regression: `_configure_iam_role` still uses `profile.arn` inside the branch "
        'where `"IamInstanceProfile" in head_node_config`. That `profile` is not defined '
        "in that branch in the buggy version, causing runtime failure."
    )

    # Ensure the branch actually propagates from the configured head instance profile
    # (not from a variable named profile).
    assert re.search(r"head_node_config\s*\[\s*['\"]IamInstanceProfile['\"]\s*\]", branch) or (
        "IamInstanceProfile" in branch and "head_node_config" in branch
    ), (
        "Expected the branch handling a user-provided IamInstanceProfile to derive the "
        "workers' instance profile from `head_node_config['IamInstanceProfile']` (or otherwise "
        "clearly reference head_node_config), not from an unrelated variable."
    )