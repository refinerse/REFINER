import types

from sky.clouds.gcp import GCP


def test_gcp_default_cpu_image_is_ubuntu_2004():
    """Default (CPU) image should explicitly specify ubuntu-2004.

    This ensures image naming is unambiguous (e.g., not just 'common-cpu').
    """
    gcp = GCP()

    # Minimal stub with the attributes accessed by make_deploy_resources_variables.
    resources = types.SimpleNamespace(
        instance_type="n1-standard-1",
        accelerators=None,
        accelerator_args=None,
        use_spot=False,
    )

    vars_dict = gcp.make_deploy_resources_variables(resources)

    assert vars_dict["image_name"] == "common-cpu-ubuntu-2004", (
        "GCP.make_deploy_resources_variables() should set the default CPU "
        "image_name to 'common-cpu-ubuntu-2004' (explicit Ubuntu 20.04). "
        f"Got: {vars_dict['image_name']!r}"
    )