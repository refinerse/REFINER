import numpy as np


def test_isin_dict_is_treated_as_single_object_element_not_iterated_over_keys():
    d = dict(a=1, b=2)

    # Correct behavior (as documented in the "after" version): non-array-like
    # containers like dict/set are converted by np.asarray into a 0-d object
    # array containing the container itself, NOT an array of its contents/keys.
    # Therefore, 'a' is not found "in" the dict via np.isin.
    res = np.isin("a", d)
    assert res.shape == (), "np.isin('a', dict(...)) should return a scalar boolean"
    assert bool(res) is False, (
        "np.isin should *not* iterate over dict keys; dict should be treated as "
        "a single object element, so np.isin('a', dict(a=1, b=2)) must be False"
    )


def test_isin_generator_is_materialized_like_sequence():
    # "Before" code attempted to special-case iterables without __getitem__
    # (e.g. generators) by materializing them into an array, making membership
    # work. The "after" version deliberately removed that conversion, so the
    # generator becomes a single object element and membership is False.
    gen = (x for x in [1, 2, 4, 8])
    res = np.isin(2, gen)
    assert res.shape == (), "np.isin(scalar, generator) should return a scalar boolean"
    assert bool(res) is False, (
        "np.isin should not special-case generators/iterables; they should be "
        "treated as a single object element (so membership is False)"
    )