import inspect
import pytest

import matplotlib.cbook as cbook


def test_check_in_list_print_supported_values_is_keyword_only():
    """
    Ensure `_print_supported_values` was made keyword-only in cbook._check_in_list.

    This is a style/API-safety change: passing the flag positionally should
    raise TypeError, but passing it as a keyword should work.
    """
    sig = inspect.signature(cbook._check_in_list)

    param = sig.parameters.get("_print_supported_values")
    assert param is not None, (
        "Expected matplotlib.cbook._check_in_list to accept an argument named "
        "'_print_supported_values'."
    )
    assert param.kind is inspect.Parameter.KEYWORD_ONLY, (
        "Expected matplotlib.cbook._check_in_list(..., *, _print_supported_values=...) "
        "so that '_print_supported_values' is keyword-only."
    )

    # Functional behavior check: positional passing should be rejected.
    with pytest.raises(TypeError, match="positional"):
        cbook._check_in_list(["a", "b"], False, arg="c")

    # Keyword passing should be accepted and influence the error message.
    with pytest.raises(ValueError) as excinfo:
        cbook._check_in_list(["a", "b"], _print_supported_values=False, arg="c")
    assert "supported values are" not in str(excinfo.value), (
        "When _print_supported_values=False, the ValueError message should not list "
        "supported values."
    )