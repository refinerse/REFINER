import re


def test_enet_cv_sample_weight_correctness_constructs_sw_contiguously():
    source = open(
        "/workspace/sklearn/linear_model/tests/test_coordinate_descent.py",
        encoding="utf-8",
    ).read()

    # Extract the body of the specific test function under review.
    m = re.search(
        r"def test_enet_cv_sample_weight_correctness\([^)]*\):(?P<body>.*?)(?=\n\ndef |\n\n@pytest)",
        source,
        flags=re.S,
    )
    assert m is not None, (
        "Could not locate `test_enet_cv_sample_weight_correctness` in "
        "/workspace/sklearn/linear_model/tests/test_coordinate_descent.py"
    )
    body = m.group("body")

    # Review comment intent: keep construction of `sw` contiguous and readable:
    # initialize `sw` (ones_like) and then immediately set the first block.
    #
    # BEFORE: `sw = np.ones_like(...)` appears early, but `sw[:n_samples] = ...`
    # happens later after other unrelated statements.
    #
    # AFTER: `sw = np.ones_like(y_with_weights)` is moved to just before the slice
    # assignment, making the two lines contiguous (ignoring comments/blank lines).
    pattern = (
        r"sw\s*=\s*np\.ones_like\(\s*y_with_weights\s*\)\s*"
        r"(?:\n\s*#.*\s*)*"
        r"\n\s*sw\s*\[\s*:\s*n_samples_per_cv\s*\]\s*=\s*rng\.randint\("
    )
    assert re.search(pattern, body) is not None, (
        "Expected `sw` to be constructed in contiguous lines inside "
        "`test_enet_cv_sample_weight_correctness`: first `sw = np.ones_like(y_with_weights)` "
        "and then immediately `sw[:n_samples_per_cv] = rng.randint(...)` (allowing only "
        "comments in between). This should fail on the pre-change code where the slice "
        "assignment occurs later, separated by unrelated statements."
    )