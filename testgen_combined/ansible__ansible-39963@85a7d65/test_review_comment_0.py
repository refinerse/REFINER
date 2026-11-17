import re


def test_loadbalancer_facts_all_subscription_listing_uses_list_without_resource_group():
    source_path = "/workspace/lib/ansible/modules/cloud/azure/azure_rm_loadbalancer_facts.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Behavior requested in review:
    # - Allow listing *all* load balancers in a subscription (resource_group can be None/omitted)
    # Runtime-significant change in code: list_items() must call list() with NO args,
    # not list(self.resource_group).
    assert (
        "response = self.network_client.load_balancers.list()" in source
    ), (
        "To support listing all load balancers in a subscription when resource_group is not provided, "
        "list_items() must call `self.network_client.load_balancers.list()` with no arguments."
    )

    assert (
        "response = self.network_client.load_balancers.list(self.resource_group)" not in source
    ), (
        "list_items() still calls `list(self.resource_group)`, which prevents listing all load balancers "
        "at subscription scope when resource_group is None/omitted."
    )


def test_loadbalancer_facts_resource_group_not_marked_required_in_docs():
    source_path = "/workspace/lib/ansible/modules/cloud/azure/azure_rm_loadbalancer_facts.py"
    source = open(source_path, "r", encoding="utf-8").read()

    # Ensure docs don't claim resource_group is required, since module supports listing all LBs.
    required_true_pattern = re.compile(
        r"resource_group:\s*\n(?:[ \t].*\n)*?[ \t]*required:\s*true",
        re.MULTILINE,
    )
    assert not required_true_pattern.search(source), (
        "DOCUMENTATION marks `resource_group` as required:true, but the module should allow omitting it "
        "to list all load balancers in the subscription."
    )