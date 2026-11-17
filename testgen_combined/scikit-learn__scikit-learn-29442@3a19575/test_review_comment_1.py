import re


def test_alpha_grid_docstring_sample_weight_has_default_none():
    source = open("/workspace/sklearn/linear_model/_coordinate_descent.py").read()

    # Locate the _alpha_grid docstring "Parameters" block to avoid matching
    # other docstrings in this large module.
    m = re.search(
        r"def _alpha_grid\([\s\S]*?\):\n\s+\"\"\"([\s\S]*?)\"\"\"",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, "Could not locate _alpha_grid function and its docstring."

    doc = m.group(1)

    # The review comment requests adding "default=None" to the docstring entry
    # for sample_weight.
    assert (
        "sample_weight : ndarray of shape (n_samples,), default=None" in doc
    ), (
        "The _alpha_grid docstring should document sample_weight with "
        "'default=None' (structural docstring consistency with signature)."
    )