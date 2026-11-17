/**
 * This test is intentionally self-contained and does not rely on the repo's Jest config,
 * which is a TypeScript config requiring ts-node in this execution environment.
 *
 * Run with:
 *   npx jest <this_file> --config '{}'
 */

import fs from 'fs';

describe('Code review change: GroupReplays access test name', () => {
  it('uses the corrected test title "should show a message when the organization doesn\'t have access to the replay feature"', () => {
    const filePath =
      '/workspace/static/app/views/organizationGroupDetails/groupReplays/groupReplays.spec.tsx';
    const source = fs.readFileSync(filePath, 'utf8');

    // After-version uses lowercased "should show a message..." (review suggestion).
    expect(source).toContain(
      `it("should show a message when the organization doesn't have access to the replay feature"`
    );

    // Before-version had a typo ("Should access message ...").
    expect(source).not.toContain(
      `it("Should access message when the organization doesn't have access to the replay feature"`
    );
    expect(source).not.toContain(
      `it('Should access message when the organization doesn't have access to the replay feature"`
    );
  });
});