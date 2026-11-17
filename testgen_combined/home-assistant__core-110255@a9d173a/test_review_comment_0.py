import re


def test_bmw_connected_drive_cleanup_updates_device_instead_of_removing() -> None:
    """Verify cleanup removes config entry id from device entry instead of removing the device.

    The review requested using device_registry.async_update_device(..., remove_config_entry_id=entry.entry_id)
    rather than device_registry.async_remove_device(device.id).
    """
    path = "/workspace/homeassistant/components/bmw_connected_drive/__init__.py"
    source = open(path, encoding="utf-8").read()

    assert (
        "async_remove_device" not in source
    ), (
        "Device cleanup must not directly remove devices via device_registry.async_remove_device(...). "
        "It should instead detach the config entry id from the device so shared devices are not deleted."
    )

    # Ensure the intended API is used (allow whitespace/newlines variations).
    pattern = re.compile(
        r"device_registry\.async_update_device\(\s*"
        r"device\.id\s*,\s*remove_config_entry_id\s*=\s*entry\.entry_id\s*"
        r"\)",
        re.DOTALL,
    )
    assert pattern.search(source), (
        "Expected device cleanup to call "
        "device_registry.async_update_device(device.id, remove_config_entry_id=entry.entry_id) "
        "for vehicles no longer assigned to the account."
    )