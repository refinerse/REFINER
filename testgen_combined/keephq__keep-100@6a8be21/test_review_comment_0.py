import os
import re


def test_parser_tests_file_removed_after_review():
    """
    After version removes /workspace/keep/parser/tests_for_parser/test_parser.py entirely.
    Before version contains it. Assert that it does NOT exist.
    """
    path = "/workspace/keep/parser/tests_for_parser/test_parser.py"
    assert not os.path.exists(path), (
        "Expected the parser tests file to be removed in the corrected ('after') version. "
        "It still exists, which indicates the repository is still in the 'before' state."
    )


def test_no_empty_string_parse_call_in_repo_sources():
    """
    Review comment indicates the empty-string parse call shouldn't be used.
    Ensure there is no .parse('') / .parse("") in the parser tests area.
    In the 'after' version the file is gone, so this should pass.
    In the 'before' version, it should fail because it contains self.parse('').
    """
    root = "/workspace/keep/parser/tests_for_parser"
    found_empty_parse_call = False
    offending_files = []

    if os.path.isdir(root):
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, "r", encoding="utf-8") as f:
                    src = f.read()
                if re.search(r"\.parse\(\s*['\"]\s*['\"]\s*\)", src):
                    found_empty_parse_call = True
                    offending_files.append(path)

    assert not found_empty_parse_call, (
        "Found a call to .parse('') or .parse(\"\") in parser tests sources, which should not be used. "
        f"Offending files: {offending_files}"
    )