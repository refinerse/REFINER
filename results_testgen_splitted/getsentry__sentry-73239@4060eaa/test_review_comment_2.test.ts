/**
 * @jest-environment node
 */

import fs from 'fs';

describe('draggableTabList typing for parsed drag/drop payload', () => {
  it('adds an explicit type annotation for the JSON-parsed drag payload (eventTab) in onInsert', () => {
    const source = fs.readFileSync(
      '/workspace/static/app/components/draggableTabs/draggableTabList.tsx',
      'utf8'
    );

    // After change, eventTab is typed as:
    // `const eventTab: {key: string; value: string} = JSON.parse(await dropItem.getText('tab'));`
    // Before change, it was untyped:
    // `const eventTab = JSON.parse(await dropItem.getText('tab'));`
    expect(source).toMatch(
      /const\s+eventTab\s*:\s*\{\s*key\s*:\s*string\s*;\s*value\s*:\s*string\s*;?\s*\}\s*=\s*JSON\.parse\s*\(/m
    );
  });
});