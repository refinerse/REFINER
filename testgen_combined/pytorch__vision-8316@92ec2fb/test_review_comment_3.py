import re


def test_jpeg_tests_freeze_rng_state_around_manual_seed_and_get_params():
    source = open("/workspace/test/test_transforms_v2.py", "r", encoding="utf-8").read()

    # The review comment requests wrapping these RNG-sensitive blocks in:
    #   with freeze_rng_state():
    #       torch.manual_seed(seed)
    #       params = transform._get_params([])
    #
    # This test enforces that `test_transform_get_params_bounds` in `TestJPEG` contains such a block.
    m = re.search(
        r"class\s+TestJPEG\s*:\s*(?P<body>.*?)(?:\nclass\s|\Z)",
        source,
        flags=re.S,
    )
    assert m, "Could not locate `class TestJPEG:` in /workspace/test/test_transforms_v2.py"
    body = m.group("body")

    m = re.search(
        r"def\s+test_transform_get_params_bounds\s*\(.*?\)\s*:\s*(?P<fn_body>.*?)(?:\n\s*def\s|\Z)",
        body,
        flags=re.S,
    )
    assert m, "Could not locate `TestJPEG.test_transform_get_params_bounds` in /workspace/test/test_transforms_v2.py"
    fn_body = m.group("fn_body")

    required_block = (
        r"with\s+freeze_rng_state\(\)\s*:\s*\n"
        r"(?:[ \t]*\n)*"
        r"[ \t]+torch\.manual_seed\(seed\)\s*\n"
        r"(?:[ \t]*\n)*"
        r"[ \t]+params\s*=\s*transform\._get_params\(\[\]\)\s*\n"
    )
    assert re.search(required_block, fn_body, flags=re.S), (
        "Expected `TestJPEG.test_transform_get_params_bounds` to wrap the RNG-sensitive calls in:\n"
        "    with freeze_rng_state():\n"
        "        torch.manual_seed(seed)\n"
        "        params = transform._get_params([])\n"
        "This ensures the test doesn't leak or depend on global RNG state."
    )