import re

FILE_PATH = "/workspace/src/backend/langflow/components/textsplitters/RecursiveCharacterTextSplitter.py"


def test_recursive_character_text_splitter_uses_build_loader_repr_from_documents():
    source = open(FILE_PATH, "r", encoding="utf-8").read()

    # The review discussion explicitly points to using:
    # langflow.utils.util.build_loader_repr_from_documents
    #
    # This test enforces that the component's repr_value is derived from documents
    # via that helper, rather than being set directly to `separators`.
    assert "build_loader_repr_from_documents" in source, (
        "Expected RecursiveCharacterTextSplitterComponent to use "
        "`langflow.utils.util.build_loader_repr_from_documents` to build the component "
        "representation from the input documents (per review comment)."
    )

    assert re.search(r"self\.repr_value\s*=\s*build_loader_repr_from_documents\s*\(", source), (
        "Expected `self.repr_value` to be set from `build_loader_repr_from_documents(...)` "
        "(i.e., repr derived from documents), not directly from `separators`."
    )