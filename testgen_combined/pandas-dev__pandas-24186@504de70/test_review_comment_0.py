import re


def test_visualization_barplot_example_suppresses_output_with_semicolon():
    source = open("/workspace/doc/source/visualization.rst", encoding="utf-8").read()

    # The review requested adding a trailing semicolon to the second line
    # (plt.axhline(...);) to suppress the object repr in the rendered HTML.
    # Verify the example has *no* semicolon on the first line, and *does* have one
    # on the second line.
    pattern = re.compile(
        r"""
        ^\s*@savefig\ bar_plot_ex\.png\s*$
        \n
        ^\s*df\.iloc\[5\]\.plot\.bar\(\)\s*;?\s*$
        \n
        ^\s*plt\.axhline\(0,\s*color='k'\)\s*;?\s*$
        """,
        re.MULTILINE | re.VERBOSE,
    )

    m = pattern.search(source)
    assert m is not None, (
        "Expected to find the bar plot example block with @savefig bar_plot_ex.png, "
        "followed by df.iloc[5].plot.bar() and plt.axhline(0, color='k') on the next lines."
    )

    df_line = m.group(0).splitlines()[-2].strip()
    axhline_line = m.group(0).splitlines()[-1].strip()

    assert not df_line.endswith(";"), (
        "The df.iloc[5].plot.bar() line should not end with ';' in this example; "
        "the review change puts the semicolon on the second line to suppress output."
    )
    assert axhline_line.endswith(";"), (
        "Expected the plt.axhline(0, color='k') line to end with ';' to suppress "
        "the plot representation in rendered HTML output."
    )