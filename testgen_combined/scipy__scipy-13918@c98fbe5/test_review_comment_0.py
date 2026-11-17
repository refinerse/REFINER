import re

import pytest


QMC_PATH = "/workspace/scipy/stats/_qmc.py"


def test_poisson_disk_variable_rename_and_grid_storage_separation():
    """
    Regression test for a refactor bug where the candidate sample variable name
    conflicted with the grid storing cell positions.

    The fixed code must:
    - store samples in a dedicated grid attribute (self.sample_grid[...] = candidate)
    - avoid indexing the candidate point as if it were the grid
      (no "np.isnan(sample[tuple(indices)][0])" pattern)
    """
    source = open(QMC_PATH, "r", encoding="utf-8").read()

    # New implementation stores accepted points into a dedicated grid array.
    assert (
        "self.sample_grid[tuple(indices)] = candidate" in source
    ), (
        "Expected PoissonDisk to store accepted candidates into a dedicated grid "
        "attribute: 'self.sample_grid[tuple(indices)] = candidate'. This guards "
        "against mixing up the candidate point with the grid of stored samples."
    )

    # Old buggy implementation accidentally indexed the *candidate* as if it were the grid.
    assert (
        "np.isnan(sample[tuple(indices)][0])" not in source
    ), (
        "Found old buggy neighborhood check pattern: "
        "'np.isnan(sample[tuple(indices)][0])'. "
        "This indicates the candidate variable is being indexed as if it were the grid."
    )

    # Ensure the class/export was renamed to PoissonDisk (functional API surface).
    assert re.search(r"\bclass\s+PoissonDisk\s*\(", source), (
        "Expected the sampler class to be named 'PoissonDisk' in scipy/stats/_qmc.py."
    )
    assert "'PoissonDisk'" in source or '"PoissonDisk"' in source, (
        "Expected 'PoissonDisk' to be present in __all__ for public API exposure."
    )