import re


def test_range_defaults_and_mypy_workaround_present_in_source():
    source = open("/workspace/src/syft/lib/python/range.py", "r", encoding="utf-8").read()

    # Key behavioral fix: when only one argument is provided (stop), Range should default start=0
    # (instead of start=None which would break builtin range()).
    assert (
        "if stop is None:" in source and "start = 0" in source
    ), (
        "Range.__init__ should default start to 0 when stop is None (single-argument range semantics). "
        "Expected to find `if stop is None:` and `start = 0` in /workspace/src/syft/lib/python/range.py."
    )

    # Key behavioral completion: step should default to 1 (builtin range default).
    # This also ensures range(start, stop, step) is valid when step not provided.
    assert re.search(r"def __init__\([\s\S]*?step:\s*Union\[Any\]\s*=\s*1", source), (
        "Range.__init__ should default step to 1. Expected signature to include `step: Union[Any] = 1` "
        "in /workspace/src/syft/lib/python/range.py."
    )

    # Review context mentions a mypy issue with range.__bool__; ensure workaround exists.
    assert (
        'mypy error: "range" has no attribute "__bool__"' in source
        or "work around" in source
        and "OverflowError" in source
    ), (
        "Expected Range.__bool__ to include the documented mypy workaround for range truthiness "
        "(try/except OverflowError around __len__)."
    )