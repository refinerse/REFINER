import re


def test_autosign_file_path_uses_tmp_path_fixture():
    """
    Verify the review change: autosign_file_path fixture uses pytest tmp_path.

    We must not import any salt modules here because the environment may raise a
    hard failure on import (version gating/logging shutdown issues). Source
    inspection is sufficient for this review comment.
    """
    with open("/workspace/tests/pytests/integration/daemons/test_masterapi.py", encoding="utf-8") as f:
        source = f.read()

    # Fixture signature should accept tmp_path (allow optional type hints/spaces)
    assert re.search(
        r"@pytest\.fixture\s*\n\s*def\s+autosign_file_path\s*\(\s*tmp_path(?:\s*:[^)]+)?\s*\)\s*:",
        source,
        flags=re.MULTILINE,
    ), (
        "Expected autosign_file_path fixture to accept tmp_path "
        "(def autosign_file_path(tmp_path):)."
    )

    # Implementation should build the path from tmp_path (allow whitespace variations)
    assert re.search(
        r"return\s+str\(\s*tmp_path\s*/\s*[\"']autosign_file[\"']\s*\)",
        source,
    ), (
        "Expected autosign_file_path to return str(tmp_path / 'autosign_file'). "
        "This ensures the path is under pytest-managed temp dirs."
    )

    # Must not use RUNTIME_VARS.TMP for autosign_file_path anymore
    assert not re.search(
        r"return\s+os\.path\.join\(\s*RUNTIME_VARS\.TMP\s*,\s*[\"']autosign_file[\"']\s*\)",
        source,
    ), (
        "autosign_file_path should not return os.path.join(RUNTIME_VARS.TMP, 'autosign_file'); "
        "it should use tmp_path so it gets cleaned up."
    )