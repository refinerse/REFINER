import re


def test_is_running_single_service_and_running_services_command_present():
    # Source-inspection only (environment can't import pytest or chia modules).
    source = open("/workspace/chia/daemon/server.py", "r", encoding="utf-8").read()

    # The "after" change restores is_running to its original single-service behavior:
    #   service_name = request["service"]
    # and adds a separate "running_services" command/handler.
    #
    # The "before" code implemented multi-service is_running with request.get("service", "*")
    # and sometimes returned {"services": [...]}, and did not have running_services.

    assert 'service_name = request["service"]' in source, (
        "Expected is_running() to require a single service via request['service'] "
        "(restored backwards-compatible behavior)."
    )

    assert 'elif command == "running_services":' in source, (
        "Expected handle_message() to dispatch the new 'running_services' command."
    )

    # Ensure the old multi-service behavior isn't present in is_running()
    assert 'request.get("service", "*")' not in source, (
        "Expected is_running() to no longer accept default service='*' (multi-service behavior)."
    )
    assert "services_to_check" not in source, (
        "Expected is_running() to no longer build a list of services to check."
    )

    # Ensure is_running doesn't return a 'services' list
    m = re.search(
        r"async def is_running\([\s\S]*?\):(?P<body>[\s\S]*?)\n\s+(?:async def|def)\s",
        source,
    )
    assert m is not None, "Failed to locate is_running() function body in /workspace/chia/daemon/server.py."
    body = m.group("body")
    assert '"services"' not in body and "'services'" not in body, (
        "Expected is_running() to return a single-service response and not include a 'services' list."
    )