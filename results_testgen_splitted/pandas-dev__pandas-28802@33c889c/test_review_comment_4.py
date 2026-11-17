import pandas.tests.reshape.test_cut as test_cut


def test_cut_bool_coercion_to_int_supports_list_box():
    """
    The repository test `test_cut_bool_coercion_to_int` should also cover plain
    Python lists as an input "box", per review comment.

    This test enforces that `list` is included in that test's parametrization by
    exercising the already-importable test function and asserting that it accepts
    `box=list` without error and with correct comparison semantics.
    """
    # The pre-change version does not support list in the compare function
    # parametrization; calling the test with list should fail (AssertionError).
    #
    # The post-change version supports list and should pass for both bins values.
    for bins in (6, 7):
        try:
            test_cut.test_cut_bool_coercion_to_int(bins=bins, box=list, compare=test_cut.tm.assert_equal)
            ran_ok = True
        except AssertionError:
            ran_ok = False

        assert (
            ran_ok
        ), "Expected `test_cut_bool_coercion_to_int` to support `box=list` and pass comparisons for list inputs"