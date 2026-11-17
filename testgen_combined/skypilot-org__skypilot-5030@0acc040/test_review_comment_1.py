from click.testing import CliRunner

import sky.cli as sky_cli


def test_local_up_password_help_mentions_passwordless_sudo_requirement():
    """Ensure the --password option's help explains when it is required."""
    runner = CliRunner()
    result = runner.invoke(sky_cli.cli, ["local", "up", "--help"])
    assert result.exit_code == 0, (
        f"Expected 'sky local up --help' to succeed; got exit_code="
        f"{result.exit_code}, output:\n{result.output}"
    )

    # Click may wrap long help text onto multiple lines; match across wrapping.
    expected_parts = [
        "Password for the ssh-user to execute sudo commands.",
        "Required only if passwordless sudo is not setup.",
    ]
    for part in expected_parts:
        assert part in result.output, (
            "The CLI help for 'sky local up --password' must include the "
            "passwordless-sudo note. Missing expected text fragment:\n"
            f"  {part!r}\n"
            "Full help output:\n"
            f"{result.output}"
        )