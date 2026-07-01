import fs from "fs";

describe("Details Gantt tab: hoveredTaskState prop should be removed when unused", () => {
  it("does not pass (even commented out) hoveredTaskState into the <Gantt /> component", () => {
    const source = fs.readFileSync(
      "/workspace/airflow/www/static/js/dag/details/index.tsx",
      "utf8"
    );

    expect(source).not.toMatch(
      /<Gantt[\s\S]*hoveredTaskState\s*=\s*\{hoveredTaskState\}/m
    );
    expect(source).not.toMatch(
      /<Gantt[\s\S]*\/\/\s*hoveredTaskState\s*=\s*\{hoveredTaskState\}/m
    );
  });
});