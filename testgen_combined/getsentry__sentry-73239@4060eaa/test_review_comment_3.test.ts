/**
 * Jest in this environment fails to start because the repo's jest.config.ts
 * requires ts-node (not installed). To keep this runnable, this file is a
 * self-contained test script (TypeScript) that can be executed directly.
 *
 * It still validates the review comment outcome: Draggable props must be typed
 * (no implicit any).
 */

import fs from 'fs';

function assert(condition: unknown, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

const FILE = '/workspace/static/app/components/draggableTabs/draggableTab.tsx';
const src = fs.readFileSync(FILE, 'utf8');

// AFTER version defines `interface DraggableProps` and uses it in the Draggable function signature.
// BEFORE version defines `function Draggable({children}) { ... }` with implicit any and no DraggableProps.
const hasDraggablePropsInterface = /\binterface\s+DraggableProps\b/.test(src);
const hasTypedDraggableSignature =
  /\bfunction\s+Draggable\s*\(\s*\{[^)]*\}\s*:\s*DraggableProps\s*\)/m.test(src);

assert(
  hasDraggablePropsInterface,
  [
    'Expected draggableTab.tsx to define explicit prop types for Draggable (avoid implicit any).',
    'Missing `interface DraggableProps`.',
  ].join('\n')
);

assert(
  hasTypedDraggableSignature,
  [
    'Expected draggableTab.tsx Draggable component to type its destructured props using DraggableProps.',
    'Missing `function Draggable(...: DraggableProps)` signature.',
  ].join('\n')
);

// If we got here, the test passes.
process.stdout.write('PASS: Draggable props are explicitly typed (no implicit any)\n');