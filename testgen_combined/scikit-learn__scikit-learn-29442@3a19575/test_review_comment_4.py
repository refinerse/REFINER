import re


def test_enet_cv_sample_weight_correctness_assigns_random_weights_to_first_group():
    source = open(
        "/workspace/sklearn/linear_model/tests/test_coordinate_descent.py",
        encoding="utf-8",
    ).read()

    # The specific requested change in the review comment is the introduction of:
    #
    #     sw = np.ones_like(y_with_weights)
    #     sw[:n_samples] = rng.randint(0, 5, size=n_samples)
    #
    # In the "before" code, the randint call is present but it is written as:
    #
    #     sw[:n_samples] = rng.randint(0, 5, size=n_samples)
    #
    # i.e. it does NOT use y_with_weights for ones_like and uses n_samples rather
    # than n_samples_per_cv.
    #
    # In the "after" code, the introduced block is:
    #
    #     sw = np.ones_like(y_with_weights)
    #     sw[:n_samples_per_cv] = rng.randint(0, 5, size=n_samples_per_cv)
    #
    # This test is intentionally strict: it requires the "_per_cv" variant and
    # the ones_like(y_with_weights) initializer to exist together.

    required_block = re.compile(
        r"sw\s*=\s*np\.ones_like\(\s*y_with_weights\s*\)\s*[\r\n]+"
        r"\s*sw\[\s*:\s*n_samples_per_cv\s*\]\s*=\s*rng\.randint\(\s*0\s*,\s*5\s*,\s*size\s*=\s*n_samples_per_cv\s*\)",
        re.MULTILINE,
    )

    assert required_block.search(source), (
        "Expected ElasticNetCV sample-weight correctness test to initialize "
        "`sw` with `np.ones_like(y_with_weights)` and then set only the first "
        "CV group's weights using "
        "`sw[:n_samples_per_cv] = rng.randint(0, 5, size=n_samples_per_cv)`."
    )

    forbidden_old_slice = re.compile(
        r"sw\[\s*:\s*n_samples\s*\]\s*=\s*rng\.randint\(\s*0\s*,\s*5\s*,\s*size\s*=\s*n_samples\s*\)"
    )
    assert not forbidden_old_slice.search(source), (
        "Found old-style weight assignment using `n_samples` "
        "(`sw[:n_samples] = rng.randint(..., size=n_samples)`). "
        "The updated code should use `n_samples_per_cv` to make it explicit that "
        "only the first CV group's samples are reweighted."
    )