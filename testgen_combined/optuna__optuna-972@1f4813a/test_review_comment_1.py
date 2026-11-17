import re


def test_hyperband_doc_example_sets_n_trials_or_timeout_in_study_optimize_call():
    source = open("/workspace/optuna/pruners/hyperband.py", "r", encoding="utf-8").read()

    # The review comment requests adding `n_trials` (or `timeout`) to stop optimization
    # in the docstring example, i.e., a call like:
    #   study.optimize(objective, n_trials=20)
    #
    # We enforce that at least one `study.optimize(...)` call in this file includes
    # either `n_trials=` or `timeout=` inside its parentheses.
    optimize_calls = list(re.finditer(r"\bstudy\.optimize\s*\((?P<args>[^)]*)\)", source, re.DOTALL))
    assert optimize_calls, "Expected to find at least one `study.optimize(...)` call in hyperband.py."

    has_stop_condition = any(
        ("n_trials" in m.group("args")) or ("timeout" in m.group("args")) for m in optimize_calls
    )

    assert has_stop_condition, (
        "The HyperbandPruner doc example should limit optimization by passing "
        "`n_trials=` or `timeout=` to `study.optimize(...)` to avoid unbounded runs. "
        "No such argument was found in any `study.optimize(...)` call."
    )