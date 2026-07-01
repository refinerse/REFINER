const fs = require("fs");

test("checkboxgroup props use tuple choices and allow number values (regression from string[] / string[][] types)", () => {
  const source = fs.readFileSync("/workspace/js/checkboxgroup/index.svelte", "utf8");

  expect(
    source.includes("export let value: (string | number)[] = [];") &&
      source.includes("export let choices: [string, number][];")
  ).toBe(
    true,
    [
      "Expected /workspace/js/checkboxgroup/index.svelte to declare:",
      '  - value: (string | number)[]',
      "  - choices: [string, number][]",
      "This ensures checkbox choices are tuples (label, value) and selected values may be numbers.",
    ].join("\n")
  );
});