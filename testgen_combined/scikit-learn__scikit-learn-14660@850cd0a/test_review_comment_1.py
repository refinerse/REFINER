import inspect

import sklearn.metrics.pairwise as pairwise


def test_pairwise_kernels_docstring_mentions_kernel_not_metric_and_single_number():
    """
    The pairwise_kernels docstring should clearly describe the callable metric
    as returning a kernel value (single number) and recommend using the string
    identifying the *kernel* (not "metric").
    """
    doc = inspect.getdoc(pairwise.pairwise_kernels)
    assert doc is not None and len(doc) > 0, "pairwise_kernels should have a non-empty docstring."

    # Key wording change requested in the review: call it a kernel, not a metric.
    assert (
        "Use the string identifying the kernel" in doc
    ), (
        "pairwise_kernels docstring should recommend 'Use the string identifying the kernel' "
        "to avoid confusion between kernels and metrics."
    )

    # Additional clarification: callable should return a single kernel value.
    assert (
        "kernel value as a single number" in doc
    ), (
        "pairwise_kernels docstring should specify that callable kernels return "
        "the corresponding kernel value as a single number."
    )