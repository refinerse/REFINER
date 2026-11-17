def test_issue_15129_test_uses_trigsimp_not_simplify():
    source = open("/workspace/sympy/simplify/tests/test_trigsimp.py", "r", encoding="utf-8").read()

    # Ensure the issue test exists (avoid false positives if file changes a lot).
    assert "def test_issue_15129_trigsimp_methods" in source, (
        "Expected the issue-15129 regression test to exist in "
        "/workspace/sympy/simplify/tests/test_trigsimp.py"
    )

    # Structural requirement from the review: do not use Matrix.simplify() here;
    # use trigsimp(...) directly.
    forbidden_patterns = [
        "assert r1.simplify()",
        "assert r2.simplify()",
        "r1.simplify()",
        "r2.simplify()",
    ]
    assert not any(p in source for p in forbidden_patterns), (
        "The issue-15129 regression test should not call Matrix.simplify(); "
        "it should assert directly on trigsimp(r1)/trigsimp(r2). Found a "
        "'.simplify()' call in the source."
    )

    # Check for the specific intended assertions.
    assert "assert trigsimp(r1) == cos(S(1)/50)" in source, (
        "Expected issue-15129 test to assert `trigsimp(r1) == cos(S(1)/50)` "
        "to avoid using expensive `.simplify()`."
    )
    assert "assert trigsimp(r2) == sin(S(3)/50)" in source, (
        "Expected issue-15129 test to assert `trigsimp(r2) == sin(S(3)/50)` "
        "to avoid using expensive `.simplify()`."
    )