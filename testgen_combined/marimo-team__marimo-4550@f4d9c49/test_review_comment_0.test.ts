import fs from "fs";

describe("useColumnExpansion hooks should avoid stale closures by using useEvent (not useCallback with empty deps)", () => {
  it("does not define callbacks via useCallback(..., []) which can capture stale state; should use useEvent instead", () => {
    const sourcePath =
      "/workspace/frontend/src/components/editor/actions/useColumnExpansion.ts";

    // If the file was removed/relocated in the 'after' version, fail with a clear message.
    expect(fs.existsSync(sourcePath)).toBe(true);

    const src = fs.readFileSync(sourcePath, "utf8");

    const hasUseCallbackEmptyDeps =
      /useCallback\s*\(\s*async\s*\(\s*\)\s*=>[\s\S]*?\}\s*,\s*\[\s*\]\s*\)/m.test(
        src,
      );

    expect(hasUseCallbackEmptyDeps).toBe(false);

    const usesUseEvent = /\buseEvent\b/.test(src);
    expect(usesUseEvent).toBe(
      true,
      "Expected implementation to use `useEvent` to avoid stale state in callbacks (review comment).",
    );
  });
});