import re


SOURCE_PATH = "/workspace/lib/ansible/modules/cloud/ovirt/ovirt_vmpool.py"


def test_examples_change_pool_name_uses_new_pool_name_and_no_spaces():
    source = open(SOURCE_PATH, "r", encoding="utf-8").read()

    # The review comment requests replacing 'new disk name' with 'new_pool_name'
    # in the EXAMPLES YAML snippet.
    assert 'name: "new disk name"' not in source, (
        "EXAMPLES should not contain the spaced placeholder name 'new disk name'. "
        "It should be replaced per style guidance."
    )

    assert 'name: "new_pool_name"' in source, (
        "EXAMPLES should demonstrate renaming the pool using a no-spaces name "
        "like 'new_pool_name' (expected to find: name: \"new_pool_name\")."
    )

    # Ensure the Change Pool Name example block exists and contains the expected name.
    m = re.search(r"# Change Pool Name.*?\n(.*?)(?=\n'''\n)", source, flags=re.S)
    assert m, "Expected to find the '# Change Pool Name' example block inside the EXAMPLES string."
    change_block = m.group(0)
    assert 'name: "new_pool_name"' in change_block, (
        "The '# Change Pool Name' example block should specifically use name: \"new_pool_name\"."
    )