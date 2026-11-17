import re


def test_inspect_prunes_hidden_and_dunder_dirs_in_os_walk():
    source = open("/workspace/src/datasets/inspect.py", "r", encoding="utf-8").read()

    # The review comment requests skipping any directory that starts with "." or "__"
    # (instead of only skipping "__pycache__").
    assert (
        'startswith((".", "__"))' in source
    ), "Expected inspect.py to prune hidden/dunder directories using dirname.startswith(('.', '__'))"

    # Ensure the old behavior is gone: explicitly checking only for __pycache__.
    assert (
        'dirname == "__pycache__"' not in source
    ), 'Expected inspect.py to no longer special-case only "__pycache__" when pruning os.walk dirnames'

    # Additionally, ensure pruning is done in-place for os.walk (dirnames[:] = ...),
    # which is the intended idiom and present in the updated code.
    assert re.search(r"dirnames\s*\[:\]\s*=\s*\[", source), (
        "Expected inspect.py to modify os.walk's dirnames in-place (dirnames[:] = ...), "
        "to ensure pruning actually affects traversal"
    )