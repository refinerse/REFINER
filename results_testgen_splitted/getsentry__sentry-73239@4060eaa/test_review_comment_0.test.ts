import fs from 'fs';
import path from 'path';

const FILE_PATH = '/workspace/static/app/components/draggableTabs/draggableTab.tsx';

/**
 * This repo's default jest.config.ts requires ts-node to parse, which is not
 * available in the execution environment for these tests.
 *
 * Running Jest with an explicit config avoids loading /workspace/jest.config.ts.
 */
export default {
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
  transform: {},
};

describe('draggableTab rules-of-hooks fix: Draggable extracted out of component', () => {
  it('does not define a nested Draggable component inside BaseDraggableTab/DraggableTab', () => {
    const src = fs.readFileSync(FILE_PATH, 'utf8');

    const hasNestedDraggableInsideBaseDraggableTab =
      /function\s+BaseDraggableTab[\s\S]*?\n\s*function\s+Draggable\s*\(/m.test(src);

    expect(hasNestedDraggableInsideBaseDraggableTab).toBe(false);
  });

  it('defines Draggable at module scope (top-level), not inside another function', () => {
    const src = fs.readFileSync(FILE_PATH, 'utf8');

    // After fix: `function Draggable(...) { ... useDrag(...) ... }` exists at top-level.
    // Before: Draggable exists but is nested, so this assertion still passes;
    // the previous test is what forces failure on the before version.
    const hasTopLevelDraggableFunction = /(^|\n)\s*function\s+Draggable\s*\(/m.test(src);

    expect(hasTopLevelDraggableFunction).toBe(true);
  });
});