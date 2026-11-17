import re


def test_separate_openai_and_aoai_config_lists_present() -> None:
    source = open("/workspace/test/agentchat/contrib/test_gpt_assistant.py", "r", encoding="utf-8").read()

    # The review requires splitting config_list into:
    # - openai_config_list filtered to api_type openai
    # - aoai_config_list filtered to api_type azure AND api_version 2024-02-15-preview
    assert "openai_config_list = autogen.config_list_from_json" in source, (
        "Expected the test file to define 'openai_config_list' (original OpenAI-only config list) "
        "via autogen.config_list_from_json, but it was not found."
    )
    assert "aoai_config_list = autogen.config_list_from_json" in source, (
        "Expected the test file to define 'aoai_config_list' (Azure OpenAI config list) "
        "via autogen.config_list_from_json, but it was not found."
    )

    # Ensure OpenAI list is still explicitly OpenAI-only (not merged with Azure).
    assert 'filter_dict={"api_type": ["openai"]}' in source, (
        "Expected openai_config_list to use filter_dict={'api_type': ['openai']} to keep the "
        "original config list OpenAI-only."
    )

    # Ensure AOAI list includes the requested api_version filter.
    assert '"api_version": ["2024-02-15-preview"]' in source, (
        "Expected aoai_config_list to include filter_dict with api_version ['2024-02-15-preview']."
    )

    # Ensure tests run the two config lists separately (looping over [openai_config_list, aoai_config_list]).
    assert re.search(r"for\s+gpt_config\s+in\s+\[\s*openai_config_list\s*,\s*aoai_config_list\s*\]\s*:", source), (
        "Expected tests to iterate separately over both config lists via "
        "'for gpt_config in [openai_config_list, aoai_config_list]:' but this pattern was not found."
    )

    # Ensure the old combined filter is not present anymore.
    assert 'filter_dict={"api_type": ["openai", "azure"]}' not in source, (
        "Did not expect a combined config list filter for both OpenAI and Azure "
        "(filter_dict={'api_type': ['openai', 'azure']}). The review requires separate lists."
    )