import re


def test_examples_use_snake_case_tag_name_without_spaces():
    source_path = "/workspace/lib/ansible/modules/cloud/ovirt/ovirt_tag.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # The review comment asks to change the example value from "new tag name" to "new_tag_name"
    # ("No spaces. s/new tag name/new_cluster_name" but the merged code uses new_tag_name).
    #
    # We verify the example block no longer contains the spaced string and does contain the
    # snake_case variant.
    assert '"new tag name"' not in source, (
        "EXAMPLES in ovirt_tag.py should not use a tag name with spaces. "
        'Expected the example to replace "new tag name" with a no-spaces snake_case name.'
    )

    assert re.search(r'name:\s*"new_tag_name"\s*$', source, flags=re.MULTILINE), (
        "EXAMPLES in ovirt_tag.py should include the updated example line "
        'name: "new_tag_name" (snake_case, no spaces).'
    )