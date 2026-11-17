import inspect

import keep.api.routes.topology as topology


def test_create_application_route_decorator_uses_multiline_formatting():
    """
    Review comment suggests formatting the @router.post("/applications", ...) decorator
    across multiple lines. This has no runtime behavior change, so we verify via source
    inspection of the function definition.
    """
    src = inspect.getsource(topology.create_application)

    assert (
        '@router.post(\n    "/applications",' in src
    ), (
        "Expected create_application to use a multi-line @router.post decorator like:\n"
        "@router.post(\\n"
        '    "/applications",\\n'
        '    description="Create a new application",\\n'
        "    response_model=TopologyApplicationDtoOut\\n"
        ")\n"
        "This should fail if the decorator remains a single-line call."
    )