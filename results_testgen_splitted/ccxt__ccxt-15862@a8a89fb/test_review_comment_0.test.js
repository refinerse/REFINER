const gemini = require('/workspace/js/gemini.js');

test('gemini.fetchMarketsFromWeb retries webGetRestApi failures (succeeds on 2nd attempt) and parses at least one market row', async () => {
    const exchange = new gemini();

    // Make retry deterministic and quick
    exchange.options['fetchMarketFromWebRetries'] = 2;

    let attempts = 0;

    // Build HTML that satisfies the parser:
    // - must contain the <h1 ...> split marker exactly once
    // - must have at least 2 occurrences of "tbody>" after the marker, because code uses tables[1]
    // - tables[1] must contain "\n<tr>\n" at least twice (rows[0] empty prefix + at least one row)
    // - each row must have at least 5 "</td>\n" splits (i.e. 4 </td>\n in the row content + the trailing part)
    const html = [
        'header',
        '<h1 id="symbols-and-minimums">Symbols and minimums</h1>',
        'anything',
        'tbody>', // tables[0]
        'tbody>', // tables[1] begins after this
        '\n<tr>\n', // rows[0] = '' (prefix before first row)
        // Row 1 (note the exact "\n<tr>\n" delimiter before each row)
        '<td>btcusd</td>\n',
        '<td>0.00001 BTC (1e-5)</td>\n',
        '<td>0.00000001 BTC (1e-8)</td>\n',
        '<td>0.01 USD</td>\n',
        '</tr>\n<tr>\n', // ensures rows.length >= 2
        // Row 2
        '<td>ethusd</td>\n',
        '<td>0.001 ETH (1e-3)</td>\n',
        '<td>0.00000001 ETH (1e-8)</td>\n',
        '<td>0.01 USD</td>\n',
        '</tr>',
    ].join('');

    exchange.webGetRestApi = async () => {
        attempts += 1;
        if (attempts === 1) {
            throw new TypeError('fetch failed');
        }
        return html;
    };

    const markets = await exchange.fetchMarketsFromWeb();

    expect(attempts).toBe(
        2,
        'fetchMarketsFromWeb should retry webGetRestApi after a failure and succeed on a subsequent attempt'
    );
    expect(Array.isArray(markets) && markets.length >= 1).toBe(
        true,
        'fetchMarketsFromWeb should parse at least one market from the HTML after a successful retry'
    );
    expect(markets[0]).toHaveProperty(
        'id',
        'fetchMarketsFromWeb should return market objects that include an id field'
    );
});