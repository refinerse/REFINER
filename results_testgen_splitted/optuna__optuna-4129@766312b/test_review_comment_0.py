import io
from argparse import Namespace
from contextlib import redirect_stdout
import os
import re

import optuna
from optuna.cli import _OptunaApp, _Studies


def _extract_table_header(stdout: str) -> str:
    # Find the first header row like: "| name | direction | ... |"
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|") and "name" in line:
            return line
    raise AssertionError(f"Could not find table header row in output:\n{stdout}")


def test_optuna_studies_hides_user_attrs_column_when_all_empty(tmp_path):
    storage_url = f"sqlite:///{os.fspath(tmp_path / 'studies.db')}"
    optuna.create_study(storage=storage_url, study_name="empty-study")

    app = _OptunaApp()
    cmd = _Studies(app=app, app_args=Namespace(storage=storage_url))
    parsed_args = Namespace(format="table", flatten=False)

    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd.take_action(parsed_args)

    header_line = _extract_table_header(buf.getvalue())

    assert not re.search(r"\buser_attrs\b", header_line), (
        "`optuna studies` should NOT include the `user_attrs` column in the TABLE header when all "
        "studies have empty user_attrs ({}). The corrected behavior is to hide it in this case."
        f"\nObserved header: {header_line}"
    )