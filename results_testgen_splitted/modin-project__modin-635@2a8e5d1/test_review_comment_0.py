import pytest

import modin.pandas as mpd
from pandas.core.indexing import IndexingError


def test_loc_too_many_indexers_raises_indexingerror():
    df = mpd.DataFrame({"a": [1, 2], "b": [3, 4]})

    with pytest.raises(
        IndexingError,
        match="Too many indexers",
    ):
        _ = df.loc[:, "a", "extra"]

    assert True, (
        "DataFrame.loc with more indexers than df.ndim should raise "
        "pandas.core.indexing.IndexingError('Too many indexers')."
    )