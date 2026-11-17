import re


def test_ovirt_cluster_examples_cluster_name_has_no_spaces():
    source = open("/workspace/lib/ansible/modules/cloud/ovirt/ovirt_cluster.py", "r", encoding="utf-8").read()

    # The review comment refers to the EXAMPLES YAML snippet for "Change cluster Name".
    # Ensure that example does not show a cluster name with spaces.
    m = re.search(
        r"#\s*Change cluster Name\s*\n"
        r"-\s*ovirt_cluster:\s*\n"
        r"(?:[ \t]+.*\n)*?"
        r"[ \t]+name:\s*(?P<q>['\"])(?P<name>.*?)(?P=q)",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, (
        "Expected to find the '# Change cluster Name' example with a quoted 'name' field "
        "in /workspace/lib/ansible/modules/cloud/ovirt/ovirt_cluster.py"
    )

    example_name = m.group("name")
    assert " " not in example_name, (
        "Cluster name in the 'Change cluster Name' example must not contain spaces. "
        f"Found name={example_name!r}."
    )