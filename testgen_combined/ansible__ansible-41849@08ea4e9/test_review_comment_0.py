import re


def test_ecs_cluster_fargate_execution_role_uses_registered_iam_role_result():
    """
    The fix is specifically in the Fargate section:
      - register the iam_role task result as iam_execution_role
      - use execution_role_arn: "{{ iam_execution_role.arn }}"
    The file may still contain other iam_role_facts tasks elsewhere; do not forbid them globally.
    """
    path = "/workspace/test/integration/targets/ecs_cluster/playbooks/roles/ecs_cluster/tasks/main.yml"
    source = open(path, encoding="utf-8").read()

    # Ensure the ecsTaskExecutionRole is created and that task is registered.
    iam_role_block = re.search(
        r"- name:\s*ensure AmazonECSTaskExecutionRolePolicy exists\s*\n"
        r"\s*iam_role:\s*\n"
        r"(?:\s+.*\n)*?"
        r"\s*<<:\s*\*aws_connection_info\s*\n"
        r"\s*register:\s*iam_execution_role\s*\n",
        source,
        flags=re.MULTILINE,
    )
    assert iam_role_block is not None, (
        "Expected the 'ensure AmazonECSTaskExecutionRolePolicy exists' iam_role task to "
        "register its result as 'iam_execution_role'."
    )

    # Ensure the Fargate task definition uses the registered role's ARN directly.
    assert 'execution_role_arn: "{{ iam_execution_role.arn }}"' in source, (
        "Expected the Fargate task definition to set execution_role_arn using the registered "
        "result directly: execution_role_arn: \"{{ iam_execution_role.arn }}\"."
    )

    # Ensure the older facts-based execution role pattern isn't used.
    assert "iam_execution_role.iam_roles.0.arn" not in source, (
        "Did not expect execution_role_arn to use the old facts-based lookup "
        "'iam_execution_role.iam_roles.0.arn'; it should use 'iam_execution_role.arn'."
    )

    # Ensure there is no ecsTaskExecutionRole facts-gathering task (the previous approach).
    # This is scoped to that specific role name to avoid failing due to other, unrelated facts tasks.
    assert re.search(
        r"- name:\s*gather facts for the ecsTaskExecutionRole\s*\n\s*iam_role_facts:\s*\n",
        source,
        flags=re.MULTILINE,
    ) is None, (
        "Did not expect a task named 'gather facts for the ecsTaskExecutionRole' using "
        "iam_role_facts; the ARN should be obtained from registering the previous iam_role task."
    )