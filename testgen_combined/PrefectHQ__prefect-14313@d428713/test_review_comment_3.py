import re


def test_dynamic_infrastructure_team_structure_bullet_updated():
    source = open("/workspace/docs/3.0rc/deploy/index.mdx", encoding="utf-8").read()

    # The review comment replaces the old bullet that began with "If your internal team structure..."
    # with a new bullet beginning "An internal organizational structure..." (potentially wrapped).
    expected_new_bullet = (
        r"-\s*An internal organizational structure in which deployment authors or runners are not members of\s*"
        r"the team that manages the infrastructure\."
    )
    assert re.search(expected_new_bullet, source, flags=re.MULTILINE), (
        "Expected the Dynamic infrastructure section to include the updated bullet:\n"
        "'- An internal organizational structure in which deployment authors or runners are not members of "
        "the team that manages the infrastructure.'\n"
        "This ensures the docs reflect the review comment change."
    )

    forbidden_old_bullet = (
        r"-\s*If your internal team structure requires that deployment authors be members of a different team\s*"
        r"than the team managing infrastructure\."
    )
    assert not re.search(forbidden_old_bullet, source, flags=re.MULTILINE), (
        "Found the old bullet starting with 'If your internal team structure requires...'. "
        "It should be replaced by the updated wording from the review comment."
    )