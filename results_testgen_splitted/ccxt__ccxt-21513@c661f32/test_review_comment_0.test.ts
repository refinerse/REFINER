const fs = require('fs');

describe('bitget fetchOHLCV: retrievable-days map should be user-overridable via options', () => {
    test('stores maxDaysPerTimeframe in this.options.fetchOHLCV (not hardcoded locally)', () => {
        const source = fs.readFileSync('/workspace/ts/src/bitget.ts', 'utf8');

        // After fix: mapping should exist in options under fetchOHLCV.maxDaysPerTimeframe
        expect(source).toContain("'maxDaysPerTimeframe'");

        // Before fix: mapping was hardcoded as a local const in fetchOHLCV
        expect(source).not.toContain('const retrievableDaysMapForSpot = {');
    });
});