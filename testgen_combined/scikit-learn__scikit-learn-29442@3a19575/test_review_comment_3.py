import re


def test_enet_cv_sample_weight_correctness_uses_renamed_n_samples_variable():
    source = open(
        "/workspace/sklearn/linear_model/tests/test_coordinate_descent.py",
        encoding="utf-8",
    ).read()

    # The style change requested in the review is to rename the local variable
    # `n_samples` to `n_samples_per_cv_group` (in the final version it is
    # `n_samples_per_cv`). This is not observable at runtime, so we assert on the
    # source code.
    #
    # We specifically check the tuple assignment line in the test body.
    before_pat = re.compile(
        r"^\s*n_splits\s*,\s*n_samples\s*,\s*n_features\s*=\s*3\s*,\s*10\s*,\s*5\s*$",
        re.MULTILINE,
    )
    after_pat = re.compile(
        r"^\s*n_splits\s*,\s*n_samples_per_cv(?:_group)?\s*,\s*n_features\s*="
        r"\s*3\s*,\s*10\s*,\s*5\s*$",
        re.MULTILINE,
    )

    assert not before_pat.search(source), (
        "Expected `n_samples` to be renamed to something like "
        "`n_samples_per_cv_group`/`n_samples_per_cv` in "
        "`test_enet_cv_sample_weight_correctness`, but found the old assignment "
        "`n_splits, n_samples, n_features = 3, 10, 5`."
    )
    assert after_pat.search(source), (
        "Expected to find the updated assignment "
        "`n_splits, n_samples_per_cv_group (or n_samples_per_cv), n_features = 3, 10, 5` "
        "in `test_enet_cv_sample_weight_correctness`."
    )