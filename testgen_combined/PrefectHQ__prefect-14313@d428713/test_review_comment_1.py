import re


def test_prefect_docker_docs_workers_link_updated():
    source = open("/workspace/docs/integrations/prefect-docker/index.mdx", "r", encoding="utf-8").read()

    # The docs should link to the docker infrastructure examples page (new, correct link)
    expected = "/3.0rc/deploy/infrastructure-examples/docker"
    assert expected in source, (
        "Expected prefect-docker docs to link to the Docker infrastructure examples page. "
        f"Missing link target: {expected}"
    )

    # Ensure we are not linking to the older/incorrect pages mentioned in the review history
    forbidden = [
        "/3.0rc/deploy/static-infra/push-runs-remote",
        "3.0rc/deploy/dynamic-infra/push-runs-remote",
        "/3.0rc/deploy/dynamic-infra/push-runs-remote",
    ]
    present_forbidden = [p for p in forbidden if p in source]
    assert not present_forbidden, (
        "prefect-docker docs still contain outdated Workers docs link(s): "
        f"{present_forbidden}. Update the link to /3.0rc/deploy/infrastructure-examples/docker."
    )

    # Optional sanity: confirm the expected link appears in the 'Examples' section line
    assert re.search(
        r"### Examples\s+See the Prefect \[Workers docs\]\(/3\.0rc/deploy/infrastructure-examples/docker\)",
        source,
        flags=re.MULTILINE,
    ), (
        "Expected the 'Examples' section to include: "
        "See the Prefect [Workers docs](/3.0rc/deploy/infrastructure-examples/docker) ..."
    )