import re


def test_hyperband_docstring_example_includes_pruning_calls():
    source = open("/workspace/optuna/pruners/hyperband.py", "r", encoding="utf-8").read()

    # The review comment requests an example objective that actually activates pruning.
    # I.e., it must call `trial.report(...)` and check `trial.should_prune()`.
    assert "trial.report" in source, (
        "HyperbandPruner docstring example should include `trial.report(...)` so that the pruner "
        "can observe intermediate values. No `trial.report` found in /workspace/optuna/pruners/hyperband.py."
    )
    assert "trial.should_prune" in source, (
        "HyperbandPruner docstring example should include `trial.should_prune()` to actually "
        "trigger pruning decisions. No `trial.should_prune` found in /workspace/optuna/pruners/hyperband.py."
    )

    # Also ensure the example shows the intended pruning behavior by raising TrialPruned.
    assert re.search(r"raise\s+optuna\.exceptions\.TrialPruned\s*\(", source), (
        "HyperbandPruner docstring example should raise `optuna.exceptions.TrialPruned()` when "
        "`trial.should_prune()` is True, to demonstrate pruning behavior."
    )