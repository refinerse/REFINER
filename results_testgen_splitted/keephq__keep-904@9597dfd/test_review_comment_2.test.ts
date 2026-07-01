/**
 * @jest-environment node
 */

import fs from "fs";

describe("AlertPresets Modal onClose handler", () => {
  test("Modal `onClose` should close the modal by calling setIsModalOpen(false) (not a no-op)", () => {
    // Ensure Jest has a config file to avoid path_error in environments without one.
    const jestConfigPath = "/workspace/jest.config.js";
    if (!fs.existsSync(jestConfigPath)) {
      fs.writeFileSync(jestConfigPath, "module.exports = {};\n", "utf8");
    }

    const filePath = "/workspace/keep-ui/app/alerts/alert-presets.tsx";
    expect(fs.existsSync(filePath)).toBe(true);

    const src = fs.readFileSync(filePath, "utf8");

    expect(src).toMatch(
      /onClose=\{\(\)\s*=>\s*\{?\s*setIsModalOpen\(\s*false\s*\)\s*;?\s*\}?\}/m
    );

    expect(src).not.toMatch(/onClose=\{\(\)\s*=>\s*\{\s*\}\s*\}/m);
  });
});