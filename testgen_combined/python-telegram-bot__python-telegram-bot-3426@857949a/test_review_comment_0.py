import re


def test_invoice_tests_do_not_use_create_task_for_invoice_calls():
    """
    Review request: revert changes where invoice-related tests started using
    asyncio.create_task without gathering; prefer awaiting directly / gathering
    for readability. This test enforces that the invoice test module does not
    use asyncio.create_task for these calls.
    """
    source = open("/workspace/tests/test_invoice.py", "r", encoding="utf-8").read()

    # Narrow to only the create_task usages that wrap send_invoice/create_invoice_link.
    create_task_send_invoice = re.search(r"asyncio\.create_task\(\s*.*send_invoice\(", source, re.S)
    create_task_create_link = re.search(
        r"asyncio\.create_task\(\s*.*create_invoice_link\(", source, re.S
    )

    assert (
        create_task_send_invoice is None and create_task_create_link is None
    ), (
        "tests/test_invoice.py should not wrap bot.send_invoice() or bot.create_invoice_link() "
        "in asyncio.create_task(...). The requested change is to revert that pattern in favor of "
        "direct awaiting / asyncio.gather for readability."
    )