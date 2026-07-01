/**
 * @jest-environment node
 */

import fs from 'fs';

describe('sessionStatusBadge crash percent denominator', () => {
  it('uses total sessions (crash + healthy) as the denominator when computing crashPercent', () => {
    const filePath =
      '/workspace/static/app/components/devtoolbar/components/releases/sessionStatusBadge.tsx';
    const src = fs.readFileSync(filePath, 'utf8');

    expect(src).toContain('const crashPercent');

    // Accept minor formatting differences while still enforcing the correct denominator.
    const correctDenominatorRegex =
      /crashSessions\s*\/\s*\(\s*crashSessions\s*\+\s*healthySessions\s*\)/;

    expect(
      correctDenominatorRegex.test(src)
    ).toBeTruthy();

    // Ensure we are not using only healthySessions as the denominator
    const wrongDenominatorRegex = /crashSessions\s*\/\s*healthySessions/;
    expect(
      wrongDenominatorRegex.test(src)
    ).toBeFalsy();
  });
});