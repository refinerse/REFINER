import numpy as np
import optuna


def test_enqueue_trial_skip_if_exists_detects_all_params_and_handles_numpy_float_nan() -> None:
    # This test targets Study._should_skip_enqueue behavior used by enqueue_trial(skip_if_exists=True).
    #
    # Regression in "before" code:
    # - It returns True as soon as it finds *any* repeated parameter (early return),
    #   even if other parameters differ.
    # - It calls np.isnan on numpy scalar types without casting, and will treat NaN as "repeated".
    #
    # Fixed in "after" code:
    # - It requires *all* params to be repeated (all(repeated_params)).
    # - It uses isinstance(param_value, Real) and casts to float for isnan/isclose checks.

    study = optuna.create_study()

    # Create an existing trial with fixed params:
    # - "a" is NaN stored as numpy float scalar
    # - "b" is 1.0
    def objective(trial: optuna.Trial) -> float:
        a = trial.suggest_float("a", -1, 1)
        b = trial.suggest_float("b", 0, 10)
        return float(b)

    study.enqueue_trial({"a": np.float64(np.nan), "b": 1.0})
    study.optimize(objective, n_trials=1)

    # Now attempt to enqueue with same "a" (NaN) but different "b".
    # Correct behavior: do NOT skip because not all params match.
    # Before behavior: will incorrectly skip because it returns True when it sees "a" repeated.
    before_n_trials = len(study.get_trials(deepcopy=False))

    study.enqueue_trial({"a": np.float64(np.nan), "b": 2.0}, skip_if_exists=True)

    after_n_trials = len(study.get_trials(deepcopy=False))

    assert (
        after_n_trials == before_n_trials + 1
    ), "enqueue_trial(skip_if_exists=True) must not skip when only some parameters match; it should skip only when *all* params are repeated (including handling of numpy float NaN)."