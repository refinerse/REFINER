const poloniex = require('/workspace/js/poloniex.js');

test('poloniex.fetchOrderBook parses alternating [price, amount] pairs starting at index 0 (even indices)', async () => {
    const exchange = new poloniex();

    // Avoid any network calls inside fetchOrderBook
    exchange.loadMarkets = async () => {
        exchange.markets = {
            'BTC/USDT': { id: 'BTC_USDT', symbol: 'BTC/USDT' },
        };
        exchange.markets_by_id = { BTC_USDT: exchange.markets['BTC/USDT'] };
        exchange.symbols = ['BTC/USDT'];
        return exchange.markets;
    };

    // Provide a deterministic order book response where:
    // asks = [price0, amount0, price1, amount1]
    // Correct parsing should include BOTH pairs.
    exchange.publicGetMarketsSymbolOrderBook = async () => ({
        time: 1659695219507,
        asks: ['10', '1', '11', '2'],
        bids: ['9', '3', '8', '4'],
        ts: 1659695219513,
    });

    const ob = await exchange.fetchOrderBook('BTC/USDT');

    expect(ob.asks).toEqual(
        [
            [10, 1],
            [11, 2],
        ]
    );

    expect(ob.bids).toEqual(
        [
            [9, 3],
            [8, 4],
        ]
    );
});