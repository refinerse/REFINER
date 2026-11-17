import re


def test_environ_settings_parametrize_uses_dict_steps():
    """Ensure test_environ_settings is structured as dict-based 'steps'.

    The review requested that initial/config/expected values be dictionaries
    (readable as steps). Since PyQt5 isn't available here, we verify the test
    structure via source inspection.
    """
    source = open("/workspace/tests/unit/config/test_qtargs.py", encoding="utf-8").read()

    # Must parametrize over init_val, config_val (dicts), not over lots of scalar/list params.
    assert (
        "@pytest.mark.parametrize('init_val, config_val'" in source
    ), (
        "Expected test_environ_settings to parametrize over 'init_val, config_val' "
        "(dict-based steps). Old version used 'config_opt, config_val, init_val, envvar, expected'."
    )

    # Must set config via attribute assignment to qt.environ, not config_stub.set_obj('qt.environ', ...)
    assert (
        "config_stub.val.qt.environ = config_val" in source
    ), (
        "Expected test_environ_settings to set config via "
        "'config_stub.val.qt.environ = config_val' for clarity."
    )

    # Must iterate dict items, not zip over envvar/init_val lists.
    assert (
        "for var, val in init_val.items():" in source
    ), "Expected initialization loop to iterate over init_val.items() (dict-based), for readability."

    # Must assert unsetting by checking key absence, not by asserting empty-string value.
    assert (
        "assert var not in os.environ" in source
    ), (
        "Expected test_environ_settings to assert unsetting by absence in os.environ "
        "(not by comparing to '')."
    )

    # Ensure we don't still have the old long parametrize signature.
    assert (
        "@pytest.mark.parametrize('config_opt, config_val, init_val, envvar, expected'" not in source
    ), "Old parametrize signature still present; expected dict-based parametrization instead."

    # Ensure we don't still use the old zip-based initialization.
    assert (
        "zip(envvar, init_val)" not in source
    ), "Old list/zip-based initialization still present; expected dict iteration."