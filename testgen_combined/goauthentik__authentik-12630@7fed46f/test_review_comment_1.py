import re


def test_send_lazy_import_is_at_top_of_function_body():
    source = open("/workspace/authentik/stages/authenticator_email/models.py", "r", encoding="utf-8").read()

    # Extract the body of `def send(self, device: "EmailDevice"):` up to the next method definition.
    m = re.search(
        r"\n\s*def\s+send\s*\(\s*self\s*,\s*device:\s*\"EmailDevice\"\s*\)\s*:\s*\n(?P<body>.*?)(?=\n\s*def\s+__str__\s*\(|\n\s*class\s+Meta\s*:)",
        source,
        flags=re.DOTALL,
    )
    assert m, "Expected to find AuthenticatorEmailStage.send() method in models.py"
    body = m.group("body")

    # Find first meaningful (non-empty, non-comment) statement in the function body.
    first_stmt = None
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        first_stmt = stripped
        break

    assert first_stmt is not None, "Expected AuthenticatorEmailStage.send() to have a non-empty body"

    assert (
        first_stmt.startswith("from authentik.stages.email.tasks import send_mails")
    ), (
        "AuthenticatorEmailStage.send() should place the lazy import at the top of the function body "
        "(first non-comment statement), per review comment. "
        f"Found first statement: {first_stmt!r}"
    )