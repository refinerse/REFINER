import inspect

import sky.clouds.service_catalog.data_fetchers.fetch_aws as fetch_aws


def test_regions_list_comment_updated_to_enable_most_regions_doc():
    """Documentation nit: comment above ALL_REGIONS should reflect 'most regions'
    (not 'all regions') and mention intersection with enabled regions.
    """
    source = open(
        "/workspace/sky/clouds/service_catalog/data_fetchers/fetch_aws.py",
        "r",
        encoding="utf-8",
    ).read()

    # Locate the ALL_REGIONS definition and inspect the nearby comment block.
    idx = source.find("ALL_REGIONS = [")
    assert idx != -1, "Expected to find the ALL_REGIONS definition in fetch_aws.py."

    prefix = source[:idx]
    # Get the last ~20 lines before ALL_REGIONS = [ to capture the comment.
    window_lines = prefix.splitlines()[-20:]
    window = "\n".join(window_lines)

    assert "Enable most of the regions" in window, (
        "Expected documentation above ALL_REGIONS to say 'Enable most of the regions' "
        "(after addressing the review nit), but it was not found near ALL_REGIONS."
    )
    assert "intersection" in window, (
        "Expected documentation above ALL_REGIONS to mention taking an intersection "
        "with enabled/user-specific regions, but 'intersection' was not found."
    )

    # Also ensure we're actually inspecting the right module path (sanity).
    assert inspect.getsourcefile(fetch_aws) == (
        "/workspace/sky/clouds/service_catalog/data_fetchers/fetch_aws.py"
    )