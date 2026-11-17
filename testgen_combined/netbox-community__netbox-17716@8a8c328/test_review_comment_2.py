import re


def test_utils_no_register_system_job_exposed_or_defined():
    """
    The merged change removes the system job registration decorator from
    netbox/netbox/utils.py. Verify it's neither exported nor defined.

    This should FAIL on the pre-merge version (which includes it) and PASS
    on the merged version (which removes it).
    """
    source = open("/workspace/netbox/netbox/utils.py", "r", encoding="utf-8").read()

    assert "register_system_job" not in source, (
        "netbox/netbox/utils.py should not expose or define register_system_job() after the "
        "decorator-based system job registration approach was removed from this module. "
        "Found 'register_system_job' in the source."
    )

    # Extra safety: ensure no function definition exists even if the name appears elsewhere.
    assert re.search(r"^\s*def\s+register_system_job\s*\(", source, flags=re.M) is None, (
        "register_system_job() function definition should be removed from netbox/netbox/utils.py."
    )