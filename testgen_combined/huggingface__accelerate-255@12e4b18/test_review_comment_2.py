import inspect

import src.accelerate.accelerator as accelerator_mod


def test_save_state_docstring_uses_scaler_not_scalar():
    """
    Style check from review: docstring and naming should refer to "scaler" (not "scalar").
    This is user-facing (help/inspect) and should be consistent.
    """
    doc = inspect.getdoc(accelerator_mod.Accelerator.save_state)
    assert doc is not None, "Expected Accelerator.save_state to have a docstring."

    assert "scaler" in doc, (
        "Expected Accelerator.save_state docstring to mention 'scaler' (as in GradScaler), "
        f"but got:\n{doc}"
    )
    assert "scalar" not in doc.lower(), (
        "Expected Accelerator.save_state docstring to avoid the typo 'scalar' and use 'scaler' instead, "
        f"but got:\n{doc}"
    )