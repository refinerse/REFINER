import re


def test_consul_kv_scheme_docs_explain_env_url_override():
    source = open("/workspace/lib/ansible/plugins/lookup/consul_kv.py", "r", encoding="utf-8").read()

    # Pull out the DOCUMENTATION YAML-ish block and then the scheme option block.
    doc_match = re.search(r'DOCUMENTATION\s*=\s*"""\n(?P<doc>.*)\n"""', source, re.S)
    assert doc_match, "Expected a DOCUMENTATION triple-quoted string in consul_kv.py"
    documentation = doc_match.group("doc")

    scheme_match = re.search(
        r"(?ms)^\s+scheme:\s*\n(?P<body>(?:^\s{8,}.*\n)+)",
        documentation,
    )
    assert scheme_match, "DOCUMENTATION must contain an 'options: scheme' entry"

    scheme_block = "scheme:\n" + scheme_match.group("body")

    # The actual change in the diff: scheme's description gained the explicit statement:
    # "If you use C(ANSIBLE_CONSUL_URL) this value will be used from there."
    # Before: description was only "Whether to use http or https" (no mention of URL/env override).
    assert "If you use C(ANSIBLE_CONSUL_URL) this value will be used from there." in scheme_block, (
        "Expected the scheme option documentation to explicitly state that scheme is taken from "
        "ANSIBLE_CONSUL_URL when that env var is used (added in the addressed review)."
    )