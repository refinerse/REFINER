import lib.ansible.modules.crypto.luks_device as luks_device


class DummyModule:
    def __init__(self, uuid_value="11111111-2222-3333-4444-555555555555"):
        self.params = {"uuid": uuid_value, "label": None}

    def get_bin_path(self, name, required):
        # Handler.__init__ requires lsblk; get_device_by_uuid requires blkid
        if name == "lsblk":
            return "/usr/bin/lsblk"
        if name == "blkid":
            return "/usr/sbin/blkid"
        raise AssertionError(f"Unexpected get_bin_path({name!r}, {required!r}) call")

    def run_command(self, cmd):
        # The review comment: must use '--uuid' (not '--uid').
        assert cmd[0] == "/usr/sbin/blkid", f"Expected blkid binary in command, got: {cmd!r}"
        assert cmd[1] == "--uuid", (
            "Handler.get_device_by_uuid() must call blkid using '--uuid' "
            "(not '--uid' and not the older '-l -t UUID=<uuid>' form). "
            f"Got command: {cmd!r}"
        )
        assert cmd[2] == self.params["uuid"], (
            "Expected get_device_by_uuid() to pass the module uuid parameter value to blkid. "
            f"Got: {cmd[2]!r}, expected: {self.params['uuid']!r}"
        )
        return (0, "/dev/sda1\n", "")


def test_get_device_by_uuid_uses_blkid_uuid_option_and_parses_stdout():
    handler = luks_device.Handler(DummyModule(uuid_value="03ecd578-fad4-4e6c-9348-842e3e8fa340"))
    dev = handler.get_device_by_uuid("ignored_argument")
    assert dev == "/dev/sda1", "Expected get_device_by_uuid() to return stripped device path from blkid stdout"