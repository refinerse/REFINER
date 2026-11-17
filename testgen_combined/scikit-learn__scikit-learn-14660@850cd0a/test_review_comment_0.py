import inspect

import sklearn.metrics.pairwise as pw


def test_pairwise_kernels_callable_doc_mentions_kernel_value_not_distance():
    """
    The pairwise_kernels docstring should describe callable metrics as returning
    a kernel value (single number), not a distance.
    """
    doc = inspect.getdoc(pw.pairwise_kernels)
    assert doc, "pairwise_kernels docstring must be present."

    # The merged ("after") docstring contains this exact phrasing.
    assert "kernel value as a single number" in doc, (
        "pairwise_kernels docstring should state that a callable metric returns "
        "'kernel value as a single number'."
    )

    # The pre-merge ("before") docstring incorrectly talked about distance.
    assert "distance between them" not in doc, (
        "pairwise_kernels docstring should not refer to 'distance between them' "
        "for callable metrics; it should refer to kernel values."
    )