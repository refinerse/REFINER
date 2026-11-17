import inspect
import re

import keep.topologies.topologies_service as ts


def test_topology_models_import_is_formatted_as_parenthesized_multiline_block():
    """
    The review comment requests reformatting a long single-line import into a
    parenthesized, multi-line import block for readability/documentation style.

    This has no runtime effect, so we verify it via source inspection.
    """
    source = inspect.getsource(ts)

    # Ensure the import exists and is the parenthesized multi-line form.
    expected_block = (
        "from keep.api.models.db.topology import (\n"
        "    TopologyApplication,\n"
        "    TopologyApplicationDtoIn,\n"
        "    TopologyApplicationDtoOut,\n"
        "    TopologyService,\n"
        "    TopologyServiceApplication,\n"
        "    TopologyServiceDependency,\n"
        "    TopologyServiceDtoOut,\n"
        ")\n"
    )
    assert expected_block in source, (
        "Expected keep.topologies.topologies_service to use a parenthesized, multi-line "
        "import block for keep.api.models.db.topology models/DTOs (as suggested in the "
        "review comment). The old single-line import should be replaced."
    )

    # And ensure the old single-line import is not present (guards against both existing).
    old_single_line = (
        "from keep.api.models.db.topology import TopologyApplication, "
        "TopologyApplicationDtoIn, TopologyApplicationDtoOut, TopologyService, "
        "TopologyServiceApplication, TopologyServiceDependency, TopologyServiceDtoOut"
    )
    assert old_single_line not in source, (
        "Found the old single-line topology import; it should be reformatted into a "
        "multi-line parenthesized import block."
    )

    # Extra robustness: also ensure we didn't simply wrap but keep everything on one line.
    assert not re.search(
        r"from keep\.api\.models\.db\.topology import\s*\(.*\)",
        source,
        flags=re.DOTALL,
    ) or "\n    TopologyApplication," in source, (
        "Topology import appears parenthesized but not properly formatted as a "
        "readable multi-line block with one name per line."
    )