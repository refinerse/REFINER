import re


def test_circleci_deploy_does_not_create_nojekyll_in_latest():
    source = open("/workspace/.circleci/config.yml", encoding="utf-8").read()

    # The review comment says the explicit creation of latest/.nojekyll is not needed
    # because it already exists in the directory containing "latest".
    #
    # Before: `touch latest/.nojekyll` exists in the deploy upload_devdocs command.
    # After:  that line is removed.
    assert "touch latest/.nojekyll" not in source, (
        "CircleCI deploy job should not create 'latest/.nojekyll' explicitly. "
        "Remove the `touch latest/.nojekyll` line from /workspace/.circleci/config.yml."
    )

    # Ensure we're checking the intended section (avoid a false pass if the deploy job vanished).
    assert re.search(r"(?m)^\s+deploy:\s*$", source), (
        "Expected to find a 'deploy' job in /workspace/.circleci/config.yml to validate "
        "the upload_devdocs command content."
    )