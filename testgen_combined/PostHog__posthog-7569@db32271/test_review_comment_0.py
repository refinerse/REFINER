import re


def test_filters_pass_team_arg_and_do_not_call_simplify_in_insert_cohort_actors_into_ch():
    source = open("/workspace/ee/clickhouse/views/cohort.py").read()

    # We specifically care about the implementation of insert_cohort_actors_into_ch
    m = re.search(
        r"def insert_cohort_actors_into_ch\(.*?\):(?P<body>.*?)(?=\n\ndef |\Z)",
        source,
        flags=re.S,
    )
    assert m, "Expected to find function definition: insert_cohort_actors_into_ch in /workspace/ee/clickhouse/views/cohort.py"
    body = m.group("body")

    # Core review requirement: callsites should pass team=cohort.team to the Filter/PathFilter/StickinessFilter
    # constructors, relying on internal simplification, and should not call .simplify() in production code.
    assert ".simplify(" not in body, (
        "insert_cohort_actors_into_ch should not call .simplify(...) explicitly; passing team=cohort.team to filter "
        "constructors should handle simplification automatically."
    )

    # Ensure team is passed to all filters used by cohort actor insertion.
    required_snippets = [
        "Filter(data=filter_data, team=cohort.team)",
        "StickinessFilter(data=filter_data, team=cohort.team)",
        "PathFilter(data=filter_data, team=cohort.team)",
    ]
    for snippet in required_snippets:
        assert snippet in body, (
            f"Expected insert_cohort_actors_into_ch to construct filters with explicit team arg ({snippet}) so callers "
            "don't need to simplify manually."
        )