import re

import keep.api.routes.topology as topology


def test_applications_get_route_decorator_is_multiline_for_style_alignment():
    """
    Review requested aligning style with other routes by formatting the @router.get
    decorator for '/applications' across multiple lines.

    This is a style-only change with no runtime behavior difference in FastAPI,
    so we verify it via simple, robust source inspection (no AST).
    """
    source = open("/workspace/keep/api/routes/topology.py", "r", encoding="utf-8").read()

    # Require a multiline decorator form like:
    # @router.get(
    #     "/applications",
    #     description="Get all applications",
    #     response_model=List[TopologyApplicationDtoOut],
    # )
    pattern = re.compile(
        r"@router\.get\(\s*\n"
        r'\s*"/applications"\s*,\s*\n'
        r'\s*description\s*=\s*"Get all applications"\s*,\s*\n'
        r"\s*response_model\s*=\s*List\[TopologyApplicationDtoOut\]\s*,?\s*\n"
        r"\s*\)\s*\n"
        r"def\s+get_applications\s*\(",
        re.MULTILINE,
    )

    assert pattern.search(source), (
        "Expected the '/applications' GET route decorator to be formatted across multiple "
        "lines (aligned with other routes), e.g. "
        "@router.get(\\n"
        '    "/applications",\\n'
        '    description="Get all applications",\\n'
        "    response_model=List[TopologyApplicationDtoOut],\\n"
        "), but it was not found in /workspace/keep/api/routes/topology.py."
    )

    # Sanity check: ensure we're inspecting the same module under test.
    assert hasattr(topology, "get_applications"), "Expected keep.api.routes.topology.get_applications to exist."