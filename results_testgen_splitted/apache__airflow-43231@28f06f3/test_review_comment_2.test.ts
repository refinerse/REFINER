import fs from "fs";

describe("DagsList sort option labels style", () => {
  it('does not label start date sorting as "(A-Z)" and instead uses "latest-earliest"', () => {
    const filePath = "/workspace/airflow/ui/src/pages/DagsList/DagsList.tsx";

    expect(fs.existsSync(filePath)).toBe(
      true,
    );

    const src = fs.readFileSync(filePath, "utf8");

    expect(
      src.includes("Last Run Start Date (A-Z)") ||
        src.includes("Start Date (A-Z)") ||
        src.includes("start_date (A-Z)"),
    ).toBe(
      false,
    );

    expect(src.toLowerCase()).toContain("latest-earliest");
  });
});