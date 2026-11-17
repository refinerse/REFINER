import os

# Must be set at import-time (before pytest loads entrypoint plugins).
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


def test_cli_options_removed_unused_backtest_path_and_added_show_pair_list():
    source = open("/workspace/freqtrade/commands/cli_options.py", "r", encoding="utf-8").read()

    assert '"backtest_path"' not in source, (
        "Expected the unused CLI option key 'backtest_path' to be removed from "
        "/workspace/freqtrade/commands/cli_options.py."
    )

    assert '"backtest_show_pair_list"' in source, (
        "Expected the CLI option key 'backtest_show_pair_list' to be present in "
        "/workspace/freqtrade/commands/cli_options.py after the change."
    )

    assert "--show-pair-list" in source, (
        "Expected the '--show-pair-list' CLI flag to be present for the new "
        "'backtest_show_pair_list' option."
    )