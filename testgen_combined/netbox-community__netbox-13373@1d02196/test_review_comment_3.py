import re

def test_azuread_map_groups_defines_logger_locally():
    """
    Regression test for review comment: `logger` has not been defined.

    The "before" code calls `logger.info(...)` inside azuread_map_groups() without defining `logger`,
    which would raise NameError at runtime. The "after" code defines a local logger via
    logging.getLogger(...) inside azuread_map_groups().
    """
    source = open("/workspace/netbox/netbox/authentication.py", "r", encoding="utf-8").read()

    # Extract the body of azuread_map_groups() in a simple, robust way (no AST parsing).
    m = re.search(
        r"(?ms)^def azuread_map_groups\([^\)]*\):\n(?P<body>(?:^[ \t]+.*\n)*)",
        source,
    )
    assert m is not None, "Expected authentication.py to define function azuread_map_groups()."

    body = m.group("body")

    assert "logger = logging.getLogger(" in body, (
        "azuread_map_groups() must define a local logger (e.g., `logger = logging.getLogger(...)`) "
        "to avoid NameError when calling logger.info/logger.error."
    )