import re


def test_async_exit_actor_test_is_not_left_commented_out():
    """
    Regression test for a review comment asking whether code should be deleted
    or uncommented ("fixed" afterwards).

    The "after" version restores the assertions in
    `test_exit_actor_async_actor_raise_immediately` that were commented out in
    the "before" version.

    This test ensures those assertions are present as live code (not commented).
    """
    source = open("/workspace/python/ray/tests/test_actor_failures.py").read()

    # Extract the body of the specific test function to avoid matching other tests.
    m = re.search(
        r"(?ms)^def test_exit_actor_async_actor_raise_immediately\(.*?\):\n(.*?)(?=^def |\Z)",
        source,
    )
    assert m, "Expected to find test_exit_actor_async_actor_raise_immediately in the file."

    body = m.group(1)

    # In the fixed version, the RayActorError expectation is active (uncommented).
    assert (
        "with pytest.raises(ray.exceptions.RayActorError) as exc_info:" in body
    ), (
        "Expected `test_exit_actor_async_actor_raise_immediately` to actively assert "
        "RayActorError via `with pytest.raises(...)`. In the buggy version this block "
        "was commented out, which the review requested to fix."
    )

    # Also ensure we aren't just matching a commented-out line.
    assert (
        "# with pytest.raises(ray.exceptions.RayActorError) as exc_info:" not in body
    ), (
        "Found the RayActorError assertion still commented out in "
        "`test_exit_actor_async_actor_raise_immediately`; it should be uncommented."
    )

    # And the post-exit verification should be active (not commented).
    assert "wait_for_condition(verify)" in body, (
        "Expected `wait_for_condition(verify)` to be executed to verify atexit handler "
        "ran; in the buggy version it was commented out."
    )
    assert "# wait_for_condition(verify)" not in body, (
        "Found `wait_for_condition(verify)` still commented out; it should be active."
    )
    assert "assert not temp_file_after_exit_actor.exists()" in body, (
        "Expected the test to assert that code after exit_actor() is not executed; "
        "in the buggy version this assertion was commented out."
    )
    assert "# assert not temp_file_after_exit_actor.exists()" not in body, (
        "Found `assert not temp_file_after_exit_actor.exists()` still commented out; "
        "it should be active."
    )