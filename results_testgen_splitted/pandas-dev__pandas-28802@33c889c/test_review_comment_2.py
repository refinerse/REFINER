import inspect

import pandas.tests.reshape.test_cut as test_cut


def test_cut_bool_coercion_to_int_param_includes_list_box():
    """
    The reviewed change expands the parametrization of test_cut_bool_coercion_to_int
    to include `list` as a `box` option (because `astype(bool)` doesn't work for lists),
    and rewrites the setup to use explicit values.

    This test asserts that the parametrized cases include a `list` entry.
    It should fail on the "before" version (no list case) and pass on the "after" version.
    """
    marks = getattr(test_cut.test_cut_bool_coercion_to_int, "pytestmark", [])
    parametrize_marks = [m for m in marks if getattr(m, "name", None) == "parametrize"]

    assert parametrize_marks, "Expected test_cut_bool_coercion_to_int to be parametrized."

    # Look for the parametrize("box, compare", [...]) mark and ensure `list` is included.
    list_included = False
    for m in parametrize_marks:
        if not m.args:
            continue
        argnames = m.args[0]
        if argnames == "box, compare" and len(m.args) >= 2:
            cases = m.args[1]
            # cases are pairs like (Series, tm.assert_series_equal), etc.
            if any(case[0] is list for case in cases):
                list_included = True
                break

    assert list_included, (
        "Expected parametrization for 'box, compare' in "
        "test_cut_bool_coercion_to_int to include a (list, ...) case, "
        "so the test covers list inputs where astype(bool) is not available.\n\n"
        f"Current source:\n{inspect.getsource(test_cut.test_cut_bool_coercion_to_int)}"
    )