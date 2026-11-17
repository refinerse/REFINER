import re


def test_rqworker_system_jobs_no_longer_use_system_enabled_and_require_interval_key():
    source = open("/workspace/netbox/core/management/commands/rqworker.py").read()

    # The review comment requests removing the redundant Meta.system_enabled attribute check and instead
    # basing scheduling on presence of an interval.
    assert "system_enabled" not in source, (
        "rqworker system job scheduling should not consult Meta.system_enabled; "
        "it should schedule based on an explicit interval definition."
    )

    # Ensure we iterate over registry['system_jobs'] items as (job, kwargs), not just values().
    assert "for job, kwargs in registry['system_jobs'].items()" in source, (
        "rqworker should iterate system_jobs as (job, kwargs) pairs from registry['system_jobs'].items()."
    )

    # Ensure interval is required via kwargs['interval'] (and TypeError raised if missing),
    # reflecting the behavioral change from Meta.system_interval.
    assert "interval = kwargs['interval']" in source, (
        "rqworker should require an explicit interval via kwargs['interval'] when scheduling system jobs."
    )
    assert "raise TypeError(\"System job must specify an interval (in minutes).\")" in source, (
        "rqworker should raise a TypeError with a clear message when a system job omits the interval."
    )

    # Ensure enqueue_once uses the kwargs dict (not Meta.system_interval).
    assert "job.enqueue_once(**kwargs)" in source, (
        "rqworker should call job.enqueue_once(**kwargs) to use the registered scheduling kwargs."
    )

    # Guard against old Meta.system_interval usage.
    assert "system_interval" not in source, (
        "rqworker should not look up Meta.system_interval; interval should come from registry kwargs."
    )