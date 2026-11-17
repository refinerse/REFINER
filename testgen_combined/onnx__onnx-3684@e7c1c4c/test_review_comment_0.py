def test_release_win_min_supported_protobuf_version_is_updated():
    # Source inspection only (no imports besides stdlib, and no pytest dependency required at import time).
    source = open("/workspace/.github/workflows/release_win.yml", "r", encoding="utf-8").read()

    step_name = "Verify ONNX with the minimum supported protobuf (from requirements.txt)"
    assert step_name in source, (
        "Expected the Windows release workflow to include the step "
        f"'{step_name}', but it was not found."
    )

    # This is the specific pattern that must change: protobuf==3.11.3 should not be used.
    assert "python -m pip install protobuf==3.11.3" not in source, (
        "Workflow still pins protobuf==3.11.3 for the 'minimum supported protobuf' verification. "
        "The review comment requested updating this (e.g., to 3.12.2)."
    )