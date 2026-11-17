import pytest

import matplotlib as mpl


def test_colormapregistry_get_cmap_invalid_type_raises_typeerror_not_unhashable():
    """
    get_cmap should behave like a transformation helper:
    - Non-str, non-Colormap, non-None inputs should raise TypeError (not leak
      underlying "unhashable type" errors from dict-style lookups).
    """
    with pytest.raises(TypeError) as excinfo:
        mpl.colormaps.get_cmap([])  # unhashable; before code leaks TypeError from dict lookup
    msg = str(excinfo.value)
    assert "get_cmap expects None" in msg, (
        "For invalid (non-str, non-Colormap, non-None) inputs, get_cmap should raise "
        "a user-facing TypeError with a clear message, not a low-level error."
    )


def test_colormapregistry_get_cmap_unknown_name_raises_valueerror_not_keyerror():
    """
    get_cmap should validate string names and raise ValueError for unknown names,
    rather than KeyError from a Mapping lookup.
    """
    with pytest.raises(ValueError):
        mpl.colormaps.get_cmap("__definitely_not_a_real_matplotlib_cmap__")