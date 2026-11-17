import re


def test_jpeg_no_torchscript_todo_comment_in_source():
    """
    The review comment requests removing the outdated TODO that claims jpeg might not be
    TorchScript-compatible.

    This is a documentation-only change, so we verify it by inspecting the source file.
    """
    source_path = "/workspace/torchvision/transforms/v2/functional/_augment.py"
    with open(source_path, "r", encoding="utf-8") as f:
        source = f.read()

    # Sanity check that we are inspecting the intended portion of the file
    assert "def jpeg(" in source, "Sanity check failed: expected to find jpeg() definition in _augment.py"

    pattern = re.compile(r"TODO:\s*this is probably not torchscript-compatible\??")
    assert (
        pattern.search(source) is None
    ), "jpeg() should not contain the outdated TorchScript TODO comment; it should be removed per review."