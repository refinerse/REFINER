import re


def test_deploy_index_heading_is_not_a_question():
    """
    The review comment requests we do not lead this page section with a question.
    Specifically, the H2 heading should be '## Deployments' (not '## What is a deployment?').
    """
    source = open("/workspace/docs/3.0rc/deploy/index.mdx", encoding="utf-8").read()

    # Find the first Markdown H2 heading in the file body
    m = re.search(r"(?m)^##\s+(.+?)\s*$", source)
    assert m is not None, "Expected docs/3.0rc/deploy/index.mdx to contain an H2 ('## ...') heading."

    first_h2_text = m.group(1).strip()

    assert (
        first_h2_text == "Deployments"
    ), f"Expected the first H2 heading to be 'Deployments' (per style guidance), but found: {first_h2_text!r}"

    assert (
        not first_h2_text.endswith("?")
    ), f"Expected the first H2 heading not to be a question, but found: {first_h2_text!r}"