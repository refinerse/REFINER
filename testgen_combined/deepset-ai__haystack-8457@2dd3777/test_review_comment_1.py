def test_from_dict_checks_only_table_format_key_for_backwards_compatibility():
    source = open("/workspace/haystack/components/converters/docx.py", "r", encoding="utf-8").read()

    # The review comment clarifies that `table_format` may be missing in older serialized pipelines,
    # so from_dict must still check for its presence before converting.
    #
    # "Before" code contains:
    #   if "init_parameters" in data and "table_format" in data["init_parameters"]:
    #
    # "After" code was simplified to assume init_parameters exists, but still checks table_format:
    #   if "table_format" in data["init_parameters"]:
    assert (
        'if "table_format" in data["init_parameters"]' in source
    ), (
        "DOCXToDocument.from_dict() should check for presence of the 'table_format' key inside "
        "data['init_parameters'] (for backwards compatibility with older serialized pipelines) "
        "before attempting to convert it."
    )

    # Ensure we no longer require checking that "init_parameters" exists (those keys are always present),
    # i.e., the old redundant guard should be removed.
    assert (
        'if "init_parameters" in data and "table_format" in data["init_parameters"]' not in source
    ), (
        "DOCXToDocument.from_dict() should not guard on the existence of 'init_parameters' anymore; "
        "it should assume data['init_parameters'] exists, but still guard on 'table_format' being present."
    )