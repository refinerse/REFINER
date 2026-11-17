import pytest

from lib.ansible.module_utils.redfish_utils import RedfishUtils


class _TestRedfishUtils(RedfishUtils):
    """Test double that avoids network and captures requested URIs."""

    def __init__(self, creds, root_uri):
        # Don't call parent __init__ (it calls _init_session etc.); keep minimal.
        self.root_uri = root_uri
        self.creds = creds
        self.requested_uris = []

    def get_request(self, uri):
        self.requested_uris.append(uri)

        # Simulate the API response the method expects.
        # If called with the UpdateService URI, return Actions directly (after-code path).
        if uri.endswith("/redfish/v1/UpdateService"):
            return {
                "ret": True,
                "data": {
                    "Actions": {
                        "#UpdateService.SimpleUpdate": {
                            "title": "SimpleUpdate",
                            "TransferProtocol@Redfish.AllowableValues": ["HTTPS"],
                        }
                    }
                },
            }

        # If called with service root, return UpdateService link (before-code path).
        if uri.endswith("/redfish/v1"):
            return {"ret": True, "data": {"UpdateService": {"@odata.id": "/redfish/v1/UpdateService"}}}

        # Any other call would be unexpected for this test.
        return {"ret": False, "msg": f"Unexpected URI requested: {uri}"}


def test_get_firmware_update_capabilities_uses_update_uri_not_hardcoded_service_root():
    """
    Ensure get_firmware_update_capabilities does not hardcode '/redfish/v1',
    but instead uses the UpdateService URI (self.update_uri) discovered earlier.
    """
    rf = _TestRedfishUtils(creds={"user": "u", "pswd": "p"}, root_uri="https://example.invalid")

    # Simulate prior discovery step: module should provide/update this value.
    rf.update_uri = "/redfish/v1/UpdateService"

    result = rf.get_firmware_update_capabilities()

    assert result.get("ret") is True, f"Expected successful result, got: {result}"
    assert rf.requested_uris, "Expected at least one GET request to be made"

    first_uri = rf.requested_uris[0]
    assert first_uri.endswith(rf.update_uri), (
        "Expected get_firmware_update_capabilities() to call get_request() with "
        "root_uri + self.update_uri as the first request (discovered UpdateService URI), "
        f"but first requested URI was: {first_uri!r}. This indicates a hardcoded '/redfish/v1' "
        "service root is being used instead of the module-provided UpdateService URI."
    )
    assert not first_uri.endswith("/redfish/v1"), (
        "get_firmware_update_capabilities() should not hardcode the Redfish service root "
        "('/redfish/v1') when update_uri is available; it should query UpdateService directly."
    )