import re


def test_xcom_sidecar_does_not_reference_airflow_core_conf_and_exposes_param():
    """
    The k8s provider utility should not read core Airflow settings (airflow.configuration.conf).
    Instead, it should allow callers (e.g. operator/hook/connection plumbing) to pass the
    sidecar image via a function parameter.
    """
    source = open(
        "/workspace/airflow/providers/cncf/kubernetes/utils/xcom_sidecar.py", encoding="utf-8"
    ).read()

    assert (
        "from airflow.configuration import conf" not in source
    ), "k8s provider code must not import core Airflow conf (airflow.configuration.conf)."

    assert (
        "conf.get(" not in source
    ), "k8s provider code must not call conf.get(); sidecar customization should be externalized."

    assert re.search(r"def\s+add_xcom_sidecar\(\s*pod\s*:\s*k8s\.V1Pod\s*,", source), (
        "add_xcom_sidecar should accept pod as first arg and include a keyword-only parameter "
        "for sidecar container image customization."
    )

    assert (
        "sidecar_container_image" in source
    ), "add_xcom_sidecar must expose a sidecar_container_image parameter (set by operator/hook/conn)."