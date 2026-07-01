/**
 * @jest-environment node
 */

import fs from "fs";

describe("ServiceNode incidents fetching performance regression guard", () => {
  test("service-node.tsx should not fetch incidents per node (no useIncidents/usePollIncidents usage)", () => {
    const candidates = [
      "/workspace/keep-ui/app/(keep)/topology/ui/map/service-node.tsx",
      // Fallback for environments where parentheses are normalized/escaped differently
      "/workspace/keep-ui/app/keep/topology/ui/map/service-node.tsx",
    ];

    const existingPath = candidates.find((p) => fs.existsSync(p));
    expect(existingPath).toBeTruthy();

    const source = fs.readFileSync(existingPath as string, "utf8");

    expect(source).not.toMatch(
      /\buseIncidents\b|\busePollIncidents\b/
    );
  });
});