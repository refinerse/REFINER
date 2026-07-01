const Huobi = require('/workspace/js/huobi.js');

describe('huobi.fetchBalance marginMode should not hijack non-spot (swap/future) balances', () => {
    test('type=swap with marginMode=cross must use contract cross-account endpoint, not spot cross-margin endpoint', async () => {
        const exchange = new Huobi({ enableRateLimit: false });

        // Avoid network/credentials usage and focus on routing logic.
        exchange.loadMarkets = async () => {};
        exchange.handleMarketTypeAndParams = (methodName, market, params) => {
            return [params.type || 'spot', params];
        };
        exchange.handleMarginModeAndParams = (methodName, params) => {
            return [params.marginMode, params];
        };

        // If the buggy "before" routing happens, it will call this spot margin method.
        exchange.spotPrivateGetV1CrossMarginAccountsBalance = async () => {
            throw new Error('BUG: spot cross-margin endpoint should NOT be called for swap type when only marginMode=cross is provided');
        };

        // The correct endpoint for linear swap cross margin
        exchange.contractPrivatePostLinearSwapApiV1SwapCrossAccountInfo = async () => {
            return { status: 'ok', data: [{ margin_asset: 'USDT', margin_balance: '1', margin_frozen: '0' }], ts: 1 };
        };

        // Ensure subtype resolves to linear (so swap + linear branch applies).
        exchange.options = exchange.options || {};
        exchange.options.defaultSubType = 'linear';

        const balance = await exchange.fetchBalance({ type: 'swap', subType: 'linear', marginMode: 'cross' });

        expect(balance).toHaveProperty(
            'USDT',
            expect.any(Object),
        );
    });
});