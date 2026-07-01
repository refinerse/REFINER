import optuna


def test_enqueue_trial_skip_if_exists_defaults_to_false() -> None:
    study = optuna.create_study()

    # Enqueue the exact same params twice without specifying skip_if_exists.
    study.enqueue_trial({"x": 1})
    study.enqueue_trial({"x": 1})

    # After the fix, skip_if_exists defaults to False, so both enqueues should be kept.
    # Before the fix, skip_if_exists defaulted to True, so the second enqueue is skipped.
    waiting_trials = [
        t for t in study.get_trials(deepcopy=False) if t.system_attrs.get("fixed_params") == {"x": 1}
    ]
    assert (
        len(waiting_trials) == 2
    ), "enqueue_trial should not skip duplicates by default (skip_if_exists must default to False)."