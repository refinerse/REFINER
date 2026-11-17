import fs from "fs";

describe("useNotebookActions section collapse/expand wording", () => {
  it("uses 'sections' (not 'columns') for collapse/expand all action labels", () => {
    const filePath =
      "/workspace/frontend/src/components/editor/actions/useNotebookActions.tsx";

    // Ensure we're reading the right file and failing with a clear message if not.
    expect(fs.existsSync(filePath)).toBe(true);

    const src = fs.readFileSync(filePath, "utf8");

    expect(src).toContain('label: "Collapse all sections"');
    expect(src).toContain('label: "Expand all sections"');

    expect(src).not.toContain('label: "Collapse all columns"');
    expect(src).not.toContain('label: "Expand all columns"');
  });
});