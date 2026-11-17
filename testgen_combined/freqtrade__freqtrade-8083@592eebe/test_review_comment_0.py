import re


def test_setup_sh_pins_setuptools_for_gym_install_in_updateenv():
    """
    The setup.sh script must *force* setuptools==65.5.0 during venv updateenv,
    instead of prompting the user to downgrade via a check_is_new_setuptools_installed function.

    This ensures installs don't fail later when gym==0.21.0 can't be built/installed with newer setuptools.
    """
    source = open("/workspace/setup.sh", "r", encoding="utf-8").read()

    # BEFORE had an interactive downgrade function and called it before case dispatch.
    assert "function check_is_new_setuptools_installed()" not in source, (
        "setup.sh should not define an interactive setuptools downgrade function. "
        "Setuptools pinning must be handled non-interactively inside updateenv."
    )
    assert "check_is_new_setuptools_installed" not in source, (
        "setup.sh should not call check_is_new_setuptools_installed; "
        "setuptools pinning must happen inside updateenv without prompting."
    )

    # AFTER pins setuptools during updateenv bootstrap.
    # Require the exact pin to 65.5.0 as part of the pip install/upgrade command.
    pin_regex = re.compile(
        r"\$\{PYTHON\}\s+-m\s+pip\s+install\s+--upgrade[^\n]*\bsetuptools==65\.5\.0\b"
    )
    assert pin_regex.search(source), (
        "setup.sh must pin setuptools to 65.5.0 during updateenv via a non-interactive command like:\n"
        "  ${PYTHON} -m pip install --upgrade ... setuptools==65.5.0\n"
        "This avoids gym install/build failures with newer setuptools."
    )