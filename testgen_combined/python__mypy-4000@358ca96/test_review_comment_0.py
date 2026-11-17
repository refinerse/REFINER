import re


def test_check_and_set_up_type_alias_has_third_rule_comment_and_early_return_structure() -> None:
    """
    Regression test for readability/behavior refactor in SemanticAnalyzer.check_and_set_up_type_alias.

    The reviewed change replaced a hard-to-read nested boolean condition with three early-return
    rules, including an explanatory comment with concrete examples under the "Third rule:" block.

    This test intentionally checks for that explanatory comment and the presence of the
    refactored "Third rule" early return (as a proxy for the behavioral restructuring).
    """
    source = open("/workspace/mypy/semanal.py", "r", encoding="utf-8").read()

    # The "after" version includes a high-level comment describing the "Third rule" and concrete
    # examples (class Model/class C/model = Model ... Type[Model]).
    assert (
        "Third rule: Non-subscripted right hand side creates a variable" in source
    ), (
        "Expected `check_and_set_up_type_alias` to include an explanatory 'Third rule' comment "
        "with examples, as requested in the review. This comment should be present after the "
        "refactor that replaced the nested boolean condition with multiple early returns."
    )

    # Ensure the refactor actually introduced the early-return condition for the third rule.
    # Keep the match flexible with whitespace/newlines.
    third_rule_pattern = re.compile(
        r"if\s+isinstance\(s\.rvalue,\s*NameExpr\)\s+and\s+non_global_scope\s+and\s+lvalue\.is_def:\s*\n"
        r"\s*#\s*Third rule:",
        re.MULTILINE,
    )
    assert third_rule_pattern.search(source), (
        "Expected an early-return `if isinstance(s.rvalue, NameExpr) and non_global_scope and "
        "lvalue.is_def:` block preceded by a '# Third rule:' comment. This structure should "
        "exist after the review-driven refactor and should not exist in the pre-refactor code."
    )