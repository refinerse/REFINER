const Exchange = require('/workspace/js/base/Exchange.js');

describe('Exchange.findBroadlyMatchedKey transpilation-safe null check', () => {
    test('should throw TypeError when string is null (only undefined is guarded)', () => {
        const exchange = new Exchange();
        const broad = { 'err': Error };

        expect(() => exchange.findBroadlyMatchedKey(broad, null)).toThrow(
            new TypeError("Cannot read properties of null (reading 'indexOf')")
        );
    });
});