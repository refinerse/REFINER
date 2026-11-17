import re


def test_managed_docs_next_steps_link_text_and_target():
    source = open(
        "/workspace/docs/3.0rc/deploy/infrastructure-examples/managed.mdx",
        encoding="utf-8",
    ).read()

    # The review requests changing the link *text* from "deployment guide" to
    # "Run flows in Docker containers" while keeping the same target URL.
    expected = (
        "Read more about creating deployments in "
        "[Run flows in Docker containers](/3.0rc/deploy/infrastructure-examples/docker/)."
    )
    assert (
        expected in source
    ), f"Expected 'Next steps' line to be updated to:\n{expected}\n\nBut it was not found."

    # Ensure we no longer call it "the deployment guide" for this link.
    old_pattern = re.compile(
        r"Read more about creating deployments in\s+the\s+\[deployment guide\]\(/3\.0rc/deploy/infrastructure-examples/docker/\)\.",
        re.MULTILINE,
    )
    assert not old_pattern.search(
        source
    ), "The managed infra doc still refers to this page as 'the deployment guide'; it should use link text 'Run flows in Docker containers'."