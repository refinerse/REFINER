import fs from "node:fs";

describe("DagsList sorting options should be centralized and include dag_id fallback", () => {
  test("DagsList imports DagSortOptions as sortOptions from src/constants/sortParams", () => {
    const dagsListPath = "/workspace/airflow/ui/src/pages/DagsList/DagsList.tsx";
    const contents = fs.readFileSync(dagsListPath, "utf8");

    expect(
      contents.includes(
        'import { DagSortOptions as sortOptions } from "src/constants/sortParams";',
      ),
    ).toBe(
      true,
      "Expected /workspace/airflow/ui/src/pages/DagsList/DagsList.tsx to import DagSortOptions as sortOptions from src/constants/sortParams (centralized sort options with dag_id fallback).",
    );
  });
});