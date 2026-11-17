import re

import lib.ansible.modules.cloud.ovirt.ovirt_template as ovirt_template


def test_no_cloud_init_persist_option_and_no_run_once_logic_for_templates():
    """
    Review request: template has no 'run-once', so remove cloud_init_persist behavior/option.
    This test asserts the module source no longer contains the cloud_init_persist option/logic.
    It should FAIL on the pre-fix code (where cloud_init_persist exists) and PASS after removal.
    """
    source_path = "/workspace/lib/ansible/modules/cloud/ovirt/ovirt_template.py"
    source = open(source_path, "r", encoding="utf-8").read()

    assert "cloud_init_persist" not in source, (
        "ovirt_template module should not implement 'cloud_init_persist' (templates have no run-once); "
        "expected all references to 'cloud_init_persist' to be removed from the module."
    )

    # Extra guard: also ensure no alias remains that implies persisting sysprep/cloud-init state:
    assert "sysprep_persist" not in source, (
        "ovirt_template module should not keep 'sysprep_persist' alias (it was tied to cloud_init_persist/run-once); "
        "expected it to be removed as well."
    )

    # And ensure no conditional still blocks updates based on that flag (a common pattern in the before code):
    assert not re.search(r"not\s+self\.param\(\s*'cloud_init_persist'\s*\)", source), (
        "ovirt_template module should not contain update_check logic gated by cloud_init_persist; "
        "expected such checks to be removed."
    )