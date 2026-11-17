import re


def test_parsr_headline_extraction_asserts_two_docs_present():
    source = open("/workspace/test/nodes/test_file_converter.py", "r", encoding="utf-8").read()

    # Extract only the body of test_parsr_converter_headline_extraction(), stopping at the next top-level "def ".
    m = re.search(
        r"^@pytest\.mark\.skipif\(sys\.platform in \[\"win32\", \"cygwin\"\], reason=\"Parsr not running on Windows CI\"\)\n"
        r"^def test_parsr_converter_headline_extraction\(\):\n"
        r"(?P<body>[\s\S]*?)(?=^\ndef |\Z)",
        source,
        flags=re.MULTILINE,
    )
    assert m is not None, "Expected to find 'test_parsr_converter_headline_extraction' in /workspace/test/nodes/test_file_converter.py"

    body = m.group("body")

    # The review requested asserting len(docs) == 2 so both expected_headlines entries are actually tested.
    assert "assert len(docs) == 2" in body, (
        "test_parsr_converter_headline_extraction should assert 'len(docs) == 2' "
        "to ensure both expected_headlines entries are tested"
    )