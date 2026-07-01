import os
import tempfile

import marimo._cli.sandbox as sandbox


def test_run_in_sandbox_uses_uv_python_not_python_version_flag():
    """
    Regression test for uv CLI flag name:
    marimo should use `--python`, not `--python-version`, when passing a
    requires-python specifier to `uv run`.
    """
    # Create a script file containing a PEP-723-style "script" block with requires-python.
    script_contents = "\n".join(
        [
            "# /// script",
            '# requires-python = ">=3.11"',
            'dependencies = ["requests"]',
            "# ///",
            "",
            "print('hello')",
            "",
        ]
    )

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        script_path = f.name
        f.write(script_contents)

    try:
        # Must run without raising on both versions (only assertions should differ).
        # We don't assert anything about the exit code.
        sandbox.run_in_sandbox(
            ["run", script_path, "--sandbox"],
            name=script_path,
        )

        # Verify behavior via robust source inspection:
        # before: used "--python-version"
        # after: uses "--python"
        source = open(
            "/workspace/marimo/_cli/sandbox.py", "r", encoding="utf-8"
        ).read()

        assert "--python-version" not in source, (
            "run_in_sandbox should not pass '--python-version' to 'uv run'; "
            "the correct uv flag is '--python'."
        )
        assert 'uv_cmd.extend(["--python", python_version])' in source, (
            "run_in_sandbox should extend the uv command with "
            '`["--python", python_version]` when a requires-python specifier is present.'
        )
    finally:
        os.unlink(script_path)