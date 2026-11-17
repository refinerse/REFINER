import inspect

import keep.api.routes.topology as topology


def test_topology_models_import_is_multiline_parenthesized():
    """
    The review comment requests changing the import of topology DTOs to a
    parenthesized multi-line form:

        from keep.api.models.db.topology import (
            TopologyApplicationDtoIn,
            TopologyApplicationDtoOut,
            TopologyServiceDtoOut,
        )

    This is a documentation/style-only change with no runtime behavior difference,
    so we verify it via source inspection of the module.
    """
    source = inspect.getsource(topology)

    expected_block = (
        "from keep.api.models.db.topology import (\n"
        "    TopologyApplicationDtoIn,\n"
        "    TopologyApplicationDtoOut,\n"
        "    TopologyServiceDtoOut,\n"
        ")\n"
    )

    assert (
        expected_block in source
    ), "Expected keep.api.routes.topology to import topology DTOs using a parenthesized multi-line import block (as suggested in the review comment)."