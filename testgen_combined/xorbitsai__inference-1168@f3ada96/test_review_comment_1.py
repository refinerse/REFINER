import re


def test_client_api_key_header_only_set_when_cluster_authed():
    source = open("/workspace/xinference/client/restful/restful_client.py", "r").read()

    # We specifically want to ensure the api_key Authorization header is only set
    # when the cluster reports auth enabled.
    #
    # Before:  if api_key is not None:
    # After:   if api_key is not None and self._cluster_authed:
    assert (
        "if api_key is not None and self._cluster_authed" in source
    ), (
        "Client.__init__ should only set the Authorization header from api_key when "
        "the cluster is authenticated. Expected condition "
        "'if api_key is not None and self._cluster_authed' to be present."
    )

    # Ensure the old, unsafe condition is not present in the Client.__init__ block.
    # (We anchor the search around the nearby header assignment to avoid false positives.)
    old_pattern = re.compile(
        r"if api_key is not None\s*:\s*\n\s*self\._headers\[\s*[\"']Authorization[\"']\s*\]\s*=",
        re.MULTILINE,
    )
    assert not old_pattern.search(source), (
        "Client.__init__ must not unconditionally set Authorization from api_key when "
        "cluster auth is disabled. Found the old pattern "
        "'if api_key is not None: self._headers[\"Authorization\"] = ...'."
    )