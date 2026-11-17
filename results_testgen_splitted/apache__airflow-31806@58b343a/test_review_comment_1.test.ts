import fs from "fs";

describe("Details tab-reset logic (bug fix): only reset when invalid tab for current selection", () => {
  it("uses tabCount-based reset logic (and removes the old buggy condition)", () => {
    const src = fs.readFileSync(
      "/workspace/airflow/www/static/js/dag/details/index.tsx",
      "utf8"
    );

    const hasOldBuggyCondition =
      src.includes("if ((!taskId || isGroup) && tabIndex > 3)") &&
      src.includes("onChangeTab(1)");

    const hasFixedTabCountLogic =
      src.includes("const tabCount") &&
      src.includes("? 4 : 3") &&
      src.includes("if (tabCount === 3 && tabIndex > 2)") &&
      src.includes("onChangeTab(1)");

    expect(hasFixedTabCountLogic).toBe(
      true
    );
    expect(hasOldBuggyCondition).toBe(
      false
    );
  });
});