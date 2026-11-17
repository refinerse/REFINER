import re


def test_debug_challenges_message_avoids_trailing_colon_after_url():
    """
    The debug-challenges prompt should avoid formatting URLs/FQDNs like
    '<value>: <token>' which encourages users to copy-paste a trailing ':'.
    The updated code prints labeled fields on separate lines, e.g.
    'URL: ...\\nExpected value: ...'.
    """
    source = open("/workspace/certbot/certbot/_internal/auth_handler.py", encoding="utf-8").read()

    # Before: f"{uri}: {token}" and f"{fqdn}: {token}"
    # After: f"URL: {uri}\nExpected value: {key_authz}" and similar for FQDN
    assert 'msg.append(f"{uri}: {token}")' not in source, (
        "Debug challenges message should not format HTTP-01 output as '{uri}: {token}' "
        "(a trailing ':' after the URL is easy to copy-paste by accident)."
    )
    assert 'msg.append(f"{fqdn}: {token}")' not in source, (
        "Debug challenges message should not format DNS-01 output as '{fqdn}: {token}' "
        "(a trailing ':' after the FQDN is easy to copy-paste by accident)."
    )

    assert re.search(r'msg\.append\(f"URL:\s*\{uri\}\\nExpected value:\s*\{', source), (
        "Expected updated HTTP-01 formatting with explicit labels on separate lines: "
        "'URL: {uri}\\nExpected value: {...}'."
    )
    assert re.search(r'msg\.append\(f"FQDN:\s*\{fqdn\}\\nExpected value:\s*\{', source), (
        "Expected updated DNS-01 formatting with explicit labels on separate lines: "
        "'FQDN: {fqdn}\\nExpected value: {...}'."
    )