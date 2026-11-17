import re


def test_hidden_dir_pruning_uses_inplace_slice_assignment_and_no_dirnames_copy_enumeration():
    source_path = "/workspace/src/datasets/download/streaming_download_manager.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # AFTER code should:
    # - prune hidden directories using in-place slice assignment (dirnames[:] = [...])
    # - NOT enumerate over a copy (dirnames[:]) inside enumerate()
    assert (
        "dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith((\".\", \"__\"))]"
        in source
    ), (
        "Expected hidden-directory pruning to be implemented via in-place slice assignment:\n"
        "    dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith((\".\", \"__\"))]\n"
        "This ensures os.walk pruning works by mutating the dirnames list in-place."
    )

    assert (
        "for i, dirname in enumerate(dirnames[:]):" not in source
    ), (
        "Did not expect iteration over a shallow copy of dirnames (dirnames[:]) in enumerate(). "
        "The fix should avoid the confusing enumerate(dirnames[:]) + del pattern."
    )

    # Also ensure the explanatory comment about why [:] is used is present (as per review).
    assert (
        "[:] for the in-place list modification required by os.walk" in source
    ), (
        "Expected an explanatory comment clarifying why [:] is used for in-place modification "
        "when pruning hidden directories during os.walk."
    )

    # Guard against leaving behind the old deletion-based approach in this block.
    # (We keep this check minimal: just ensure there isn't a 'del dirnames[' in the relevant area.)
    assert (
        "del dirnames[" not in source
    ), "Did not expect deletion-based pruning (e.g., 'del dirnames[i]') to remain in the implementation."