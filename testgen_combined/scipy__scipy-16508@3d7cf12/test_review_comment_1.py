import re


def test_rgi_nonscalar_values_2_loops_over_all_trailing_entries():
    """
    The review requested restructuring `test_nonscalar_values_2` to cover *all*
    entries across two trailing dimensions (e.g. 2*3=6), not just the last dim.

    We enforce this by source inspection:
    - the test must be restricted to num_trailing_dims = 2
    - and it must contain a nested loop over the last two axes
      (i in range(values.shape[-2]) and j in range(values.shape[-1]))
      with indexing values[..., i, j]
    """
    source = open("/workspace/scipy/interpolate/tests/test_rgi.py", "r", encoding="utf-8").read()

    # Ensure the test is no longer parametrized over num_trailing_dims
    assert 'pytest.mark.parametrize("num_trailing_dims"' not in source, (
        "Expected test_nonscalar_values_2 to be restructured to fixed "
        "num_trailing_dims=2 (not parametrized over a range), per review comment."
    )

    # Ensure num_trailing_dims is explicitly set to 2 in the RGI test.
    assert re.search(r"\bnum_trailing_dims\s*=\s*2\b", source), (
        "Expected test_nonscalar_values_2 to set num_trailing_dims=2 explicitly."
    )

    # Ensure there is a nested loop over both trailing dimensions in the RGI test.
    # (Before code only loops over values.shape[-1] and indexes values[..., j].)
    assert "for i in range(values.shape[-2])" in source and "for j in range(values.shape[-1])" in source, (
        "Expected nested loops over both trailing dimensions in test_nonscalar_values_2 "
        "(i over values.shape[-2], j over values.shape[-1]) to cover all trailing entries."
    )

    # Ensure values are sliced with two trailing indices.
    assert "values[..., i, j]" in source, (
        "Expected indexing values[..., i, j] inside the nested loops to test all "
        "entries across the two trailing dimensions."
    )