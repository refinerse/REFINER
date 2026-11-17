import fs from "fs";

describe("DagsList sort UI placement and options (review comment)", () => {
  it('keeps the "sort-by-select" only for card view and removes last_run_state sorting', () => {
    const srcPath = "/workspace/airflow/ui/src/pages/DagsList/DagsList.tsx";

    const src = fs.readFileSync(srcPath, "utf8");

    expect(src).toContain(
      'data-testid="sort-by-select"',
    );

    // Select must be conditionally rendered only for card display (not always visible).
    expect(src).toContain(
      '{display === "card" ? (',
    );

    // "Sort by last run state" must be removed in favor of start_date sorting.
    expect(src).not.toContain(
      "last_run_state",
    );
  });
});