import fs from "fs";

describe("useColumnExpansion hooks API consolidation", () => {
  test("file exists and defines a combined hook `useSectionCollapse` returning { expandAllSection, collapseAllSection }", () => {
    const modulePath =
      "/workspace/frontend/src/components/editor/actions/useColumnExpansion.ts";

    expect(
      fs.existsSync(modulePath),
    ).toBe(true);

    const src = fs.readFileSync(modulePath, "utf8");

    expect(src).toContain("useSectionCollapse");
    expect(src).toContain("collapseAllSection");
    expect(src).toContain("expandAllSection");
  });
});