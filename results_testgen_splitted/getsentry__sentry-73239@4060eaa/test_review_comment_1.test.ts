/**
 * Use a plain .ts Jest test (no TS config) that only reads the source file.
 * This avoids Jest trying to load /workspace/jest.config.ts (which requires ts-node).
 */

import fs from 'fs';

describe('draggableTab style cleanup: remove unused guide classnames', () => {
  test('draggableTab.tsx no longer contains the react-aria guide classname strings', () => {
    const filePath = '/workspace/static/app/components/draggableTabs/draggableTab.tsx';
    const src = fs.readFileSync(filePath, 'utf8');

    // These classname tokens existed in the "before" version and should be absent in the "after" version.
    const forbiddenTokens = [
      'drop-indicator',
      'drop-target',
      'focus-visible',
      'draggable',
      'dragging',
    ];

    for (const token of forbiddenTokens) {
      expect(src).not.toContain(
        token
      );
    }

    // "option" is too generic to ban as a raw substring; ban it only when used as a classname token.
    expect(src).not.toMatch(/\bclassName\s*=\s*{[^}]*\boption\b[^}]*}/m);
  });
});