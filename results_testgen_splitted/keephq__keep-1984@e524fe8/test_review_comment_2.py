import inspect

import keep.api.routes.topology as topology


def test_applications_endpoints_use_specific_exceptions_not_generic_exception():
    """
    Review requested: "use more specified exceptions here".
    Verify runtime-visible behavior by ensuring the route functions no longer
    catch a generic `Exception` in their source.
    """
    funcs = [
        topology.get_applications,
        topology.create_application,
        topology.update_application,
        topology.delete_application,
    ]

    for fn in funcs:
        src = inspect.getsource(fn)
        assert (
            "except Exception" not in src
        ), f"{fn.__name__} should not catch generic Exception; it should catch specific domain exceptions instead."