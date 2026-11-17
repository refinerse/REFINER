import re


def test_no_debug_tasks_left_in_alb_listener_integration_playbook():
    """
    Style regression test: the integration task file should not contain
    leftover Ansible 'debug' tasks that were used during development.

    This fails on the pre-fix version where multiple debug blocks exist, and
    passes once those debug statements are removed.
    """
    path = "/workspace/test/integration/targets/elb_application_lb/tasks/test_modifying_alb_listeners.yml"
    source = open(path, "r", encoding="utf-8").read()

    # Match typical Ansible task snippets like:
    #   - name:
    #     debug:
    #       msg: "{{ alb }}"
    #
    # as well as any other debug task in this file.
    debug_task_re = re.compile(r"(?m)^[ \t]*debug:[ \t]*$", re.MULTILINE)
    matches = list(debug_task_re.finditer(source))

    assert not matches, (
        "Expected no Ansible 'debug:' tasks in "
        f"{path}, but found {len(matches)} occurrence(s). "
        "Remove leftover debug statements from the integration test playbook."
    )