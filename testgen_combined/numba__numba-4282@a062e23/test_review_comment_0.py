import re


def test_pysignature_wraps_valueerror_and_includes_original_message():
    source = open("/workspace/numba/utils.py", "r", encoding="utf-8").read()

    # Ensure we're looking at the funcsigs fallback wrapper (not inspect.signature).
    assert "from funcsigs import signature as _pysignature" in source, (
        "Expected numba.utils to define a funcsigs-based signature fallback "
        "using '_pysignature'."
    )

    # The behavior change requested in the review is: when funcsigs.signature
    # raises ValueError (e.g. for parameter name '.0'), the wrapper should
    # catch it and raise UnsupportedError including the *original* error text.
    #
    # We test for a robust code pattern:
    #   - `except ValueError as e:` (captures the exception object)
    #   - message construction referencing the caught exception (`e.` or `str(e)`)
    #
    # BEFORE: `except ValueError:` and message doesn't use the exception.
    assert re.search(r"except\s+ValueError\s+as\s+e\s*:", source), (
        "pysignature wrapper should capture the ValueError as a variable "
        "(expected 'except ValueError as e:') so the original funcsigs message "
        "can be included in UnsupportedError."
    )

    # Ensure the caught exception is actually used in the error message.
    # This is tolerant to different formatting styles (e.message, str(e), % e, etc.).
    wrapper_block = re.search(
        r"def\s+pysignature\s*\(.*?\):(?P<body>[\s\S]*?)BoundArguments\.apply_defaults",
        source,
    )
    assert wrapper_block, (
        "Could not locate the pysignature wrapper function body in numba.utils.py "
        "for inspection."
    )
    body = wrapper_block.group("body")

    assert ("e.message" in body) or re.search(r"\bstr\s*\(\s*e\s*\)", body) or re.search(
        r"%\s*\(\s*[^)]*\be\b[^)]*\)", body
    ) or re.search(r"%\s*[^%\n]*\be\b", body), (
        "pysignature wrapper should include the original funcsigs ValueError text "
        "in the UnsupportedError message (expected to reference the caught exception "
        "e.g. via 'e.message' or 'str(e)')."
    )