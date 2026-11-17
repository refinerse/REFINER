import fs from 'fs';

describe('binance.ts editSpotOrder refactor: remove redundant spot/swap branching', () => {
    test('editSpotOrder should no longer declare a `let response` and should use a single `const response = await privatePostOrderCancelReplace(...)` call', () => {
        const source = fs.readFileSync('/workspace/ts/src/binance.ts', 'utf8');

        // Isolate editSpotOrder method text to avoid false positives from other methods.
        const start = source.indexOf('async editSpotOrder');
        expect(start).toBeGreaterThanOrEqual(0);

        const braceOpen = source.indexOf('{', start);
        expect(braceOpen).toBeGreaterThanOrEqual(0);

        let depth = 0;
        let end = -1;
        for (let i = braceOpen; i < source.length; i++) {
            const ch = source[i];
            if (ch === '{') depth++;
            else if (ch === '}') {
                depth--;
                if (depth === 0) {
                    end = i + 1;
                    break;
                }
            }
        }
        expect(end).toBeGreaterThan(braceOpen);

        const body = source.slice(braceOpen, end);

        // Key behavioral/code change:
        // BEFORE: `let response = undefined;` then conditional branches, assigning to `response`.
        // AFTER:  `const response = await this.privatePostOrderCancelReplace (payload);` (single path) and no `let response`.
        expect(body).not.toMatch(
            /\blet\s+response\s*=\s*undefined\s*;/m,
        );

        expect(body).toMatch(
            /\bconst\s+response\s*=\s*await\s+this\.privatePostOrderCancelReplace\s*\(/m,
        );
    });
});