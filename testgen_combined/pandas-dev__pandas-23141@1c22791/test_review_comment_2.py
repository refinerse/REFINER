def test_from_frame_squeeze_tests_removed_or_parametrized():
    source = open("/workspace/pandas/tests/indexes/multi/test_constructor.py").read()

    # This repository change removed the two redundant squeeze-related tests from
    # the "before" version. Enforce that they no longer exist as standalone tests.
    #
    # Before: test_from_frame_with_squeeze + test_from_frame_with_no_squeeze exist.
    # After: those tests are gone (and may or may not be replaced by a param test).
    assert "def test_from_frame_with_squeeze" not in source, (
        "Standalone test 'test_from_frame_with_squeeze' should be removed/squashed "
        "per review comment (e.g. via parametrization)."
    )
    assert "def test_from_frame_with_no_squeeze" not in source, (
        "Standalone test 'test_from_frame_with_no_squeeze' should be removed/squashed "
        "per review comment (e.g. via parametrization)."
    )