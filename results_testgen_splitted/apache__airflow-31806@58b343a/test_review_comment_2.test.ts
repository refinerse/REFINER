/**
 * Self-contained Jest test file.
 *
 * NOTE: This repo may not ship a Jest config at /workspace, and `npx jest` can fail
 * unless invoked with `--config`. This test creates a minimal Jest config file at the
 * repo root if one is not present, so the test can run cleanly.
 */

import fs from "fs";
import path from "path";

const WORKSPACE_ROOT = "/workspace";
const chartPath = "/workspace/airflow/www/static/js/dag/details/gantt/Chart.tsx";

function ensureJestConfigExists() {
  const candidateNames = [
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "jest.config.cjs",
    "jest.config.cts",
    "jest.config.json",
  ];
  const hasConfig = candidateNames.some((name) =>
    fs.existsSync(path.join(WORKSPACE_ROOT, name))
  );
  if (hasConfig) return;

  // Minimal config so `npx jest <this_file>` doesn't error with "Could not find a config file"
  const configPath = path.join(WORKSPACE_ROOT, "jest.config.js");
  const configContents = `module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)'],
  transform: {},
};\n`;

  fs.writeFileSync(configPath, configContents, "utf8");
}

beforeAll(() => {
  ensureJestConfigExists();
});

describe("Chart.tsx refactor: extract complex inline JSX into a dedicated component", () => {
  test("Chart should define at least one additional React component (refactor away from fully inlined JSX)", () => {
    expect(fs.existsSync(chartPath)).toBe(
      true,
      `Expected source file to exist at absolute path: ${chartPath}`
    );

    const src = fs.readFileSync(chartPath, "utf8");

    // Structural outcome of the refactor: at least one additional component defined
    // in this file besides Chart (PascalCase component declaration).
    // Before: only `const Chart = (...) => { ... }`
    // After: extracted component like `const TaskRow = ...` or `function TaskTooltip(...) { ... }`
    const componentDeclMatches = src.match(
      /\b(?:const|function)\s+[A-Z][A-Za-z0-9_]*\s*(?:=\s*\(|\()/g
    );

    const count = componentDeclMatches?.length ?? 0;

    expect(count).toBeGreaterThan(
      1,
      `Expected Chart.tsx to define an extracted React component (e.g. TaskRow/TaskTooltip/TaskBar) in addition to Chart. Found ${count} component declaration(s) matching 'const|function <PascalCase>'.`
    );
  });
});