import re

import lib.ansible.modules.cloud.docker.docker_image_info  # noqa: F401


def test_documentation_markup_uses_C_not_O_for_pull_source():
    """
    The module DOCUMENTATION should use Ansible doc markup C(...) for literal values.
    The reviewed typo was O(pull) which should be C(pull).
    """
    source = open("/workspace/lib/ansible/modules/cloud/docker/docker_image_info.py", "r", encoding="utf-8").read()

    assert "O(pull)" not in source, (
        "Found typo 'O(pull)' in docker_image_info DOCUMENTATION; expected it to be fixed to 'C(pull)'."
    )
    assert "C(pull)" in source, (
        "Expected corrected documentation markup 'C(pull)' to be present in docker_image_info DOCUMENTATION."
    )

    # Keep the check focused on the reviewed sentence to avoid false positives elsewhere.
    doc_line_match = re.search(r"set to (O|C)\(pull\)", source)
    assert doc_line_match, "Expected to find documentation text containing 'set to C(pull)' in the module source."
    assert doc_line_match.group(1) == "C", (
        "Expected the documentation sentence to say 'set to C(pull)' (code formatting), not 'O(pull)'."
    )