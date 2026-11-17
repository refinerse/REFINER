import re


def test_update_user_uses_optional_user_type_annotation():
    source_path = "/workspace/src/backend/langflow/services/database/models/user/crud.py"
    source = open(source_path, "r", encoding="utf-8").read()

    assert "def update_user" in source, "Expected update_user to be defined in crud.py"

    # Match across newlines/indentation in the function signature.
    # The after version has:
    # def update_user(
    #     user_db: Optional[User], user: ...
    pattern = r"user_db:\s*Optional\s*\[\s*User\s*\]"
    assert re.search(pattern, source, flags=re.MULTILINE | re.DOTALL), (
        "Expected update_user to annotate user_db as Optional[User] (allowing missing user). "
        "This should be present in the function signature."
    )

    # Ensure we didn't keep the old Union[User, None] annotation for user_db.
    assert not re.search(r"user_db:\s*Union\s*\[\s*User\s*,\s*None\s*\]", source), (
        "update_user should not annotate user_db as Union[User, None] anymore; "
        "it should use Optional[User]."
    )