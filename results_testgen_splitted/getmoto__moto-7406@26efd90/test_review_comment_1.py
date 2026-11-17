import inspect

import moto.route53domains.models as models


def test_route53domains_models_does_not_use_pep604_union_operator_in_type_hints():
    """
    Moto still supports Python 3.8, so this module should not use PEP604 unions
    (the `|` operator) in annotations (ex: `int | None`).
    """
    source = inspect.getsource(models)

    assert (
        " | " not in source
    ), "moto.route53domains.models should not use the PEP604 `|` union operator in type hints (Python 3.8 compatibility)."