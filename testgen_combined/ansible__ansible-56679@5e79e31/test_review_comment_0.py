import inspect

import lib.ansible.modules.system.hostname as hostname


def test_use_argument_choices_come_from_strats_keys():
    """
    Style regression test: the 'use' argument's choices in AnsibleModule
    should be derived from STRATS.keys(), not duplicated as a literal list.
    """
    src = inspect.getsource(hostname.main)

    assert "STRATS.keys()" in src, (
        "Expected hostname.main() to define the 'use' parameter with "
        "choices=STRATS.keys() to avoid duplicating the strategy list."
    )

    assert "choices=['generic'" not in src, (
        "Expected hostname.main() to avoid a hardcoded literal choices list for 'use'; "
        "it should reference STRATS.keys() instead."
    )