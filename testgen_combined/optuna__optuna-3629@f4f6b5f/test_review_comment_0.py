import optuna


def test_should_skip_enqueue_requires_all_params_to_match_not_any() -> None:
    # Regression test for enqueue duplicate detection.
    #
    # BEFORE: `_should_skip_enqueue` returned True as soon as *any* param matched (early return),
    # which incorrectly skipped enqueue even if other params differed.
    #
    # AFTER: It only returns True if *all* params are repeated (all(repeated_params)).
    study = optuna.create_study()

    # Existing trial with two fixed params.
    study.enqueue_trial({"x": 1.0, "y": 2.0})

    # New params share only "x" but differ in "y".
    # Correct behavior: should NOT skip, because not all params match.
    should_skip = study._should_skip_enqueue({"x": 1.0, "y": 3.0})

    assert (
        should_skip is False
    ), "Enqueue should be skipped only when *all* params match an existing trial; matching a single param must not trigger skipping."