import pytest

from sympy import Q, ask
from sympy.assumptions.ask import Predicate
from sympy.abc import x


def test_ask_custom_predicate_does_not_crash_and_returns_none_with_irrelevant_assumption():
    """
    Regression test for the original issue: passing user-defined predicates
    into ask() should not raise KeyError during the "quick known_facts_dict"
    lookup from assumptions.

    Use an assumption (~Q.odd(x)) that is a single-literal clause (so the
    relevant quick-lookup code runs), but which should NOT imply anything about
    the custom predicate. Therefore the correct return value is None.
    """
    Custom = Predicate("custom_user_predicate_for_regression")

    # Single-literal clause involving a known predicate; should not imply Custom(x).
    assumptions = ~Q.odd(x)

    # Before fix: this path could raise KeyError internally depending on the
    # structure; the regression is that it must not crash.
    res = ask(Custom(x), assumptions)

    assert res is None, (
        "ask(Custom(x), ~Q.odd(x)) should not raise and should return None, "
        "because the assumption is unrelated to the custom predicate. "
        "This exercises the fast-path lookup code that previously could raise "
        "KeyError for user-defined predicates."
    )