import re


def test_fixture_renamed_to_code_editor():
    source = open(
        "/workspace/spyder/plugins/editor/widgets/tests/test_folding.py",
        "r",
        encoding="utf-8",
    ).read()

    assert re.search(r"@pytest\.fixture\(\)\s*\ndef\s+code_editor\s*\(", source), (
        "Expected a pytest fixture named `code_editor` to be defined in "
        "/workspace/spyder/plugins/editor/widgets/tests/test_folding.py"
    )

    assert "def get_fold_levels" not in source, (
        "Expected the old fixture `get_fold_levels` to be removed/renamed to "
        "`code_editor` in /workspace/spyder/plugins/editor/widgets/tests/test_folding.py"
    )