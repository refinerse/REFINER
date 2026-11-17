# Self-contained source-inspection test.
# NOTE: This file is intentionally runnable without pytest installed.
# It uses plain asserts and does not import pandas or pytest.

import re


def test_groupby_squeeze_no_default_branch_resets_to_false():
    source = open("/workspace/pandas/core/frame.py", encoding="utf-8").read()

    # After change: when squeeze is left as no_default, it must be set to False
    # to preserve prior behavior.
    #
    # Before version: has "if squeeze is not no_default: warnings.warn(...)" but
    # does NOT have an "else: squeeze = False" branch.
    pattern = re.compile(
        r"def\s+groupby\([\s\S]*?\):[\s\S]*?"
        r"if\s+squeeze\s+is\s+not\s+no_default:\s*[\s\S]*?warnings\.warn\([\s\S]*?\)\s*"
        r"[\s\S]*?else:\s*\n\s*squeeze\s*=\s*False",
        re.MULTILINE,
    )
    assert pattern.search(source), (
        "DataFrame.groupby should set `squeeze = False` when `squeeze` is left as no_default. "
        "Expected to find an `else: squeeze = False` branch paired with the "
        "`if squeeze is not no_default:` deprecation-warning check."
    )

    # After change: the resolved squeeze value should also be forwarded.
    assert "squeeze=squeeze" in source, (
        "DataFrame.groupby should pass the resolved `squeeze` value through to DataFrameGroupBy "
        "(expected `squeeze=squeeze` in the constructor call)."
    )


if __name__ == "__main__":
    # Allow running as a script: `python test_file.py`
    test_groupby_squeeze_no_default_branch_resets_to_false()
    print("OK")