import re


def test_inspect_prunes_hidden_and_dunder_dirs_in_os_walk():
    source = open("/workspace/src/datasets/inspect.py", "r", encoding="utf-8").read()

    # The review asks to ignore directories that start with "." and "__" in the os.walk pruning logic.
    # The addressed code uses an in-place modification pattern:
    #   dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith((".", "__"))]
    #
    # Before: it only removed "__pycache__" via deletion.
    assert "__pycache__" not in source, (
        "inspect.py should no longer hardcode pruning only '__pycache__' directories; "
        "it should prune all hidden ('.*') and dunder ('__*') directories."
    )

    # Check both functions were updated (inspect_dataset and inspect_metric).
    pattern = r"dirnames\[:\]\s*=\s*\[dirname\s+for\s+dirname\s+in\s+dirnames\s+if\s+not\s+dirname\.startswith\(\(\s*\"\.\",\s*\"__\"\s*\)\)\s*\]"
    matches = re.findall(pattern, source)
    assert len(matches) == 2, (
        "Expected both inspect_dataset and inspect_metric to prune os.walk by setting "
        'dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith((".", "__"))]. '
        f"Found {len(matches)} occurrence(s)."
    )