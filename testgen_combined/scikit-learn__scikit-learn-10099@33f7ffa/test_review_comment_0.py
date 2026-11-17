import re


def test_distinct_clusters_warning_uses_convergencewarning():
    source = open("/workspace/sklearn/cluster/k_means_.py", "r", encoding="utf-8").read()

    # Must import ConvergenceWarning from sklearn.exceptions
    assert "from ..exceptions import ConvergenceWarning" in source, (
        "Expected k_means_.py to import ConvergenceWarning from sklearn.exceptions "
        "for the 'distinct clusters < n_clusters' warning."
    )

    # Must warn using ConvergenceWarning (not RuntimeWarning) for the distinct clusters case
    warn_block_pattern = re.compile(
        r"distinct_clusters\s*=\s*len\(set\(best_labels\)\)\s*[\s\S]*?"
        r"if\s+distinct_clusters\s*<\s*n_clusters\s*:\s*[\s\S]*?"
        r"warnings\.warn\([\s\S]*?ConvergenceWarning[\s\S]*?stacklevel=2\)",
        re.MULTILINE,
    )
    assert warn_block_pattern.search(source), (
        "Expected k_means to compute distinct_clusters and emit warnings.warn(..., "
        "ConvergenceWarning, stacklevel=2) when distinct_clusters < n_clusters."
    )

    # Guard against the old behavior explicitly
    assert "Possibly due to duplicate points in X\", RuntimeWarning" not in source, (
        "The distinct-clusters warning should no longer use RuntimeWarning."
    )