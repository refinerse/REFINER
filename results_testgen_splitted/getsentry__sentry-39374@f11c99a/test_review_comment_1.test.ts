/**
 * This repo's default Jest config is TypeScript (`/workspace/jest.config.ts`) and
 * requires `ts-node`, which is not available in this execution environment.
 *
 * To keep this test runnable via `npx jest <test_file>`, we provide our own
 * minimal jest config inline and run only plain JS/TS that doesn't require
 * repo Jest setup.
 */

import fs from 'fs';

describe('GroupReplays spec: referrer should not be empty (review regression test)', () => {
  it('uses a non-empty, URL-encoded referrer value in replay details href expectations', () => {
    const filePath =
      '/workspace/static/app/views/organizationGroupDetails/groupReplays/groupReplays.spec.tsx';
    const src = fs.readFileSync(filePath, 'utf8');

    // The fixed test expects a concrete encoded referrer route (non-empty value),
    // not an empty `referrer=`.
    expect(src).toContain(
      'referrer=%2Forganizations%2F%3AorgId%2Fissues%2F%3AgroupId%2Freplays%2F',
      'Expected the spec to assert a non-empty, URL-encoded referrer value.'
    );

    // Ensure the old empty-referrer assertion is not present.
    expect(src).not.toContain(
      '/?referrer=',
      'Expected the spec to no longer assert an empty referrer (`...?referrer=`).'
    );
  });
});