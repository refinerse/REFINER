import fs from "fs";

describe("AlertPresets review: remove comments", () => {
  test("keep-ui/app/alerts/alert-presets.tsx should not contain the temporary commented-out debug line", () => {
    const filePath = "/workspace/keep-ui/app/alerts/alert-presets.tsx";
    expect(fs.existsSync(filePath)).toBe(
      true
    );

    const src = fs.readFileSync(filePath, "utf8");

    expect(src).not.toContain('// console.log("HELLO WORLD");');
  });
});