# This repository's runtime environment has a broken pytest dependency chain (typing_extensions),
# so we must NOT import pytest. This file is still compatible with pytest collection because
# it only uses plain `assert` statements.
#
# The test uses source inspection only, per instructions.

def test_running_services_added_and_is_running_not_overloaded_with_list_or_wildcard():
    source = open("/workspace/chia/daemon/server.py", "r", encoding="utf-8").read()

    # The review outcome was: do NOT overload `is_running` with list/wildcard parsing;
    # instead add a new `running_services` command.
    assert 'elif command == "running_services":' in source, (
        "Expected handle_message() to route a new 'running_services' RPC command. "
        "This should exist after the review fix."
    )
    assert "async def running_services" in source, (
        "Expected a new WebSocketServer.running_services() coroutine to exist after the review fix."
    )

    # `is_running` should preserve legacy behavior: require a single 'service' field (no default '*').
    assert 'service_name = request["service"]' in source, (
        "Expected is_running() to require request['service'] (single service), preserving the old API."
    )

    # Ensure the previously introduced multi-service behavior is NOT present in `is_running`.
    forbidden_snippets = [
        'request.get("service", "*")',  # wildcard default
        'service.split(",")',           # comma-separated parsing
        '"services": responses',        # multi-service response payload
        "services_to_check",            # loop-based multi-check logic variable
    ]
    for snippet in forbidden_snippets:
        assert snippet not in source, (
            f"Did not expect snippet {snippet!r} in server.py after the fix. "
            "Multi-service listing should be handled by the new running_services command, "
            "not by overloading is_running."
        )