/**
 * @jest-environment node
 */

import fs from 'fs';

describe('iOS getting started docs - Replay snippet should not enable experimental view renderer by default', () => {
  it('does not include enableExperimentalViewRenderer=true in ios.tsx snippets', () => {
    const source = fs.readFileSync(
      '/workspace/static/app/gettingStartedDocs/apple/ios.tsx',
      'utf8'
    );

    // After the fix, the iOS replay snippet no longer opts into the experimental view renderer.
    // Before the fix, it did include this line, so this assertion must fail on the "before" code.
    expect(source).not.toContain(
      'options.sessionReplay.enableExperimentalViewRenderer = true'
    );
  });
});