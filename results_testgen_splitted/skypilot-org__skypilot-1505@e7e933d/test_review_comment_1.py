import importlib

import pandas as pd

import sky.clouds.service_catalog.data_fetchers.fetch_aws as fetch_aws


def test_images_fetcher_accepts_regions_param_and_sorts_output():
    """After change:
    - get_all_regions_images_df(regions) accepts explicit regions
    - output is sorted by ['Tag', 'Region'].

    Before change:
    - get_all_regions_images_df() has no 'regions' parameter (TypeError).
    """
    importlib.reload(fetch_aws)

    # Patch Ray + remote function to avoid starting Ray / serializing tasks.
    # (The environment may have Ray/pydantic incompatibilities.)
    unsorted_rows = [
        ("skypilot:gpu-ubuntu-2004", "us-west-2", "ubuntu", "20.04", "ami-2", "20221101"),
        ("skypilot:gpu-ubuntu-2004", "us-east-1", "ubuntu", "20.04", "ami-1", "20221101"),
        ("skypilot:k80-ubuntu-1804", "us-west-2", "ubuntu", "18.04", "ami-4", "20211208"),
        ("skypilot:k80-ubuntu-1804", "us-east-1", "ubuntu", "18.04", "ami-3", "20211208"),
    ]

    # Save originals for cleanup.
    original_ray_get = fetch_aws.ray.get
    original_get_image_row = fetch_aws._get_image_row

    # Make ray.get deterministic and offline.
    fetch_aws.ray.get = lambda _workers: unsorted_rows

    # Make _get_image_row.remote(...) not schedule Ray tasks.
    class _FakeRemote:
        def remote(self, *args, **kwargs):
            return None

    fetch_aws._get_image_row = _FakeRemote()
    try:
        regions = {"us-west-2", "us-east-1"}

        # Key behavior: after version accepts regions arg; before raises TypeError.
        df = fetch_aws.get_all_regions_images_df(regions)

        assert isinstance(df, pd.DataFrame), (
            "Expected get_all_regions_images_df(regions) to return a pandas DataFrame."
        )

        expected = df.sort_values(["Tag", "Region"]).reset_index(drop=True)
        got = df.reset_index(drop=True)
        assert got.equals(expected), (
            "Expected get_all_regions_images_df(regions) to sort output by ['Tag', 'Region']."
        )
    finally:
        fetch_aws.ray.get = original_ray_get
        fetch_aws._get_image_row = original_get_image_row