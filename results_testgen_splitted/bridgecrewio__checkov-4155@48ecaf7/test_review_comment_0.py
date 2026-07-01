import pytest

from checkov.common.models.enums import CheckResult
from checkov.terraform.checks.resource.azure.KeyVaultDisablesPublicNetworkAccess import (
    KeyVaultDisablesPublicNetworkAccess,
)


def test_key_vault_network_acls_without_ip_rules_should_fail_when_public_access_not_explicitly_disabled():
    """
    Behavior change: simply having 'network_acls' present should NOT make the check pass
    unless it contains non-empty 'ip_rules' (or public_network_access_enabled is False).
    """
    check = KeyVaultDisablesPublicNetworkAccess()

    # public_network_access_enabled omitted => defaults to True on Azure
    # network_acls exists but has no ip_rules configured => should FAIL
    conf = {
        "network_acls": [
            {
                # intentionally no "ip_rules"
                "default_action": ["Deny"],
                "bypass": ["AzureServices"],
            }
        ]
    }

    result = check.scan_resource_conf(conf)

    assert (
        result == CheckResult.FAILED
    ), "Expected FAILED when public network access is not explicitly disabled and network_acls has no ip_rules; mere presence of network_acls should not PASS."