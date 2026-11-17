import re

def test_slice_track_filters_starting_outside_shapes():
    source = open("/workspace/cvat/apps/annotation/annotation.py", "r", encoding="utf-8").read()

    # The review fix adds a helper that drops leading outside==True shapes after slicing.
    # We assert that this filtering logic exists in _slice_track.
    assert "def filter_track_shapes(shapes):" in source, (
        "Expected AnnotationIR._slice_track to define filter_track_shapes() to drop leading "
        "shapes with outside==True in the sliced segment."
    )

    # Verify the key behavior: count and drop leading outside shapes, but keep at least one.
    required_snippets = [
        "if s['outside']",
        "drop_count += 1",
        "if drop_count == len(shapes):",
        "drop_count -= 1",
        "return shapes[drop_count:]",
    ]
    for snippet in required_snippets:
        assert snippet in source, (
            f"Expected filtering logic for leading outside shapes in _slice_track. "
            f"Missing snippet: {snippet!r}"
        )

    # Ensure the old behavior (blindly inserting interpolated shapes at boundaries) is gone.
    # Before fix: loop over interpolated_shapes and insert/append when frame==start/stop.
    assert not re.search(r"for shape in interpolated_shapes:\s*\n\s*if shape\['frame'\] == start", source), (
        "Old _slice_track implementation inserts interpolated shape at start without filtering; "
        "expected updated implementation that filters leading outside shapes."
    )