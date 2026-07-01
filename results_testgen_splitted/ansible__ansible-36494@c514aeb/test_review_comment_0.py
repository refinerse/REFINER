import lib.ansible.modules.network.nxos.nxos_vrf as nxos_vrf


class _FakeModule:
    def __init__(self, state="present", purge=False):
        self.params = {"state": state, "purge": purge}


def test_map_obj_to_commands_does_not_emit_global_no_vni_when_creating_new_vrf():
    """
    Style-driven behavior check: when creating a *new* VRF (obj not in have),
    map_obj_to_commands() should not contain a redundant/always-true style check
    that injects 'no vni ...' commands based on unrelated existing VRFs.

    Before: if commands: if vni: for h in have: if h.get('vni'): insert 'no vni ...'
    After:  that block is removed (only handles vni removal when modifying an existing VRF).
    """
    module = _FakeModule(state="present", purge=False)

    want = [
        {
            "name": "NEWVRF",
            "admin_state": "up",
            "vni": "5000",
            "rd": None,
            "description": None,
            "interfaces": [],
            "state": "present",
        }
    ]

    # 'have' includes some other VRF that already has a VNI configured.
    # The buggy/undesired behavior in the "before" version is to emit a
    # global 'no vni ...' while creating NEWVRF.
    have = [
        {"name": "OTHERVRF", "admin_state": "up", "vni": "6000", "rd": "", "description": "", "interfaces": []}
    ]

    commands = nxos_vrf.map_obj_to_commands((want, have), module)

    assert all(not cmd.startswith("no vni ") for cmd in commands), (
        "Creating a new VRF must not emit 'no vni ...' based on unrelated existing VRFs; "
        "this indicates the redundant always-true style check is still present. "
        f"Commands were: {commands}"
    )