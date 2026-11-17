import os


def test_batch_retcode_docstring_no_longer_claims_multiple_modules():
    """
    Enforce review comment via source inspection: `test_batch_retcode` is not
    running multiple modules, so its docstring must not claim it does.
    """
    path = "/workspace/tests/pytests/integration/cli/test_batch.py"
    assert os.path.exists(path), f"Expected source file to exist at {path}"

    with open(path, encoding="utf-8") as f:
        source = f.read()

    # Locate the `test_batch_retcode` function
    func_anchor = "def test_batch_retcode("
    idx = source.find(func_anchor)
    assert idx != -1, "Could not find `def test_batch_retcode(` in the source file"

    # Extract its docstring using simple string operations
    doc_start = source.find('"""', idx)
    assert (
        doc_start != -1
    ), "Could not find the opening docstring triple-quote for `test_batch_retcode`"

    doc_end = source.find('"""', doc_start + 3)
    assert (
        doc_end != -1
    ), "Could not find the closing docstring triple-quote for `test_batch_retcode`"

    doc = source[doc_start + 3 : doc_end]

    assert (
        "running multiple modules at the same time works in batch" not in doc
    ), (
        "`test_batch_retcode` docstring still claims it tests running multiple modules, "
        "but that test executes only a single module. The docstring should describe retcode behavior instead."
    )

    assert "correct retcode" in doc, (
        "Expected `test_batch_retcode` docstring to be updated to describe retcode behavior "
        "(e.g., include the phrase 'correct retcode')."
    )