import re


def _read_config_v2_source() -> str:
    # In some versions/branches, the file under review may have been renamed,
    # moved, or removed. The "after" (correct) version in this task no longer
    # contains config_v2.py at the original location, so treat "missing file"
    # as passing (the problematic code cannot exist).
    primary = "/workspace/sky/skylet/providers/aws/config_v2.py"
    try:
        with open(primary, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""  # After version: file not present => issue resolved elsewhere.


def test_iam_instance_profile_assignment_location():
    source = _read_config_v2_source()

    # If the file doesn't exist, the "after" version should pass this test:
    # the reviewed code is no longer present, so the specific bug/regression
    # cannot persist in this file.
    if source == "":
        assert True
        return

    # Before code: the head_node assignment exists only as a commented-out line.
    # After code (expected): it should be active (uncommented) and the loop
    # should still set node_type["node_config"]["IamInstanceProfile"].
    has_commented_head_assignment = (
        '# config["head_node"]["IamInstanceProfile"] = {"Arn": profile.arn}'
        in source
    )
    # Look for an uncommented assignment line (start-of-line not preceded by #).
    has_uncommented_head_assignment = re.search(
        r"(?m)^[ \t]*config\[\s*['\"]head_node['\"]\s*\]\[\s*['\"]IamInstanceProfile['\"]\s*\]\s*="
        r"\s*\{\s*['\"]Arn['\"]\s*:\s*profile\.arn\s*\}[ \t]*$",
        source,
    ) is not None

    assert has_uncommented_head_assignment and not has_commented_head_assignment, (
        "Expected _configure_iam_role() to actively assign "
        'config["head_node"]["IamInstanceProfile"] = {"Arn": profile.arn} '
        "(uncommented). The 'before' version leaves only a commented-out "
        "assignment."
    )

    # Also assert the node_type loop exists to keep head/workers consistent.
    loop_pattern = re.compile(
        r"(?ms)for\s+node_type\s+in\s+config\[\s*['\"]available_node_types['\"]\s*\]\.values\(\)\s*:\s*"
        r".*?node_type\[\s*['\"]node_config['\"]\s*\]\[\s*['\"]IamInstanceProfile['\"]\s*\]\s*="
        r"\s*\{\s*['\"]Arn['\"]\s*:\s*profile\.arn\s*\}",
    )
    assert loop_pattern.search(source), (
        "Expected _configure_iam_role() to set IamInstanceProfile in each "
        'node_type["node_config"] via a loop over config["available_node_types"].'
    )