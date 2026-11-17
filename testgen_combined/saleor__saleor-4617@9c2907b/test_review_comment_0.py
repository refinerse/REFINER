def test_send_user_password_reset_email_moved_to_account_emails_and_not_defined_locally():
    source = open("/workspace/saleor/graphql/account/mutations/base.py").read()

    assert (
        "from ....account.emails import send_user_password_reset_email" in source
    ), (
        "Expected `send_user_password_reset_email` to be imported from "
        "`saleor/account/emails.py` (account.emails), so it can be reused outside "
        "GraphQL mutations."
    )

    assert (
        "def send_user_password_reset_email" not in source
    ), (
        "Expected `send_user_password_reset_email` to be moved out of "
        "`saleor/graphql/account/mutations/base.py` (no local function definition)."
    )


def test_request_password_reset_uses_shared_validate_storefront_url_helper():
    source = open("/workspace/saleor/graphql/account/mutations/base.py").read()

    assert (
        "from ....core.utils.url import validate_storefront_url" in source
    ), (
        "Expected `validate_storefront_url` to be imported and used, instead of "
        "inline URL parsing/host validation in the mutation module."
    )

    assert "validate_storefront_url(redirect_url)" in source, (
        "Expected RequestPasswordReset.perform_mutation to call "
        "`validate_storefront_url(redirect_url)`."
    )

    assert "validate_host" not in source and "urlparse" not in source, (
        "Expected the old inline validation based on `urlparse`/`validate_host` to be "
        "removed in favor of `validate_storefront_url`."
    )