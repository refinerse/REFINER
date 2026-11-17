import re


def test_argmin_argmax_dtype_precedence_order_matches_fix():
    source = open("/workspace/cupy/core/_routines_statistics.pyx", "r", encoding="utf-8").read()

    # The fix changes the dtype precedence iteration order for argmin/argmax
    # from 'bhilq' (wrong) to 'qlihb' (correct, matching NumPy default choice).
    #
    # We assert both _argmin and _argmax use the fixed order. This test fails
    # on the buggy code (which uses 'bhilq') and passes after the fix.
    expected = "for r in 'qlihb' for d in '?BhHiIlLqQ'"
    unexpected = "for r in 'bhilq' for d in '?BhHiIlLqQ'"

    assert expected in source, (
        "Expected _argmin/_argmax dtype precedence order to be fixed to 'qlihb' "
        "(so int64 'q' is preferred when dtype=None), but the fixed pattern "
        "was not found in /workspace/cupy/core/_routines_statistics.pyx."
    )
    assert unexpected not in source, (
        "Found the old buggy dtype precedence order 'bhilq' in "
        "/workspace/cupy/core/_routines_statistics.pyx; this would pick a "
        "smaller integer return type than intended when dtype=None."
    )

    # Ensure the expected pattern is used in BOTH argmin and argmax definitions.
    # (Do not try to parse; just count occurrences of the fixed generator clause.)
    n = len(re.findall(re.escape(expected), source))
    assert n >= 2, (
        "Expected the fixed dtype precedence generator clause to appear at least "
        "twice (for both _argmin and _argmax), but found it only "
        f"{n} time(s)."
    )