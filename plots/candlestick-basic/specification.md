# candlestick-basic: Basic Candlestick Chart

## Description

A candlestick chart displays open, high, low, and close (OHLC) price data for financial instruments over time. Each candlestick shows the price range within a specific period, with the body indicating the open-close range and the wicks (shadows) showing the high-low range. Color coding distinguishes bullish (price increase) from bearish (price decrease) periods, making it easy to identify trends and price patterns at a glance.

## Applications

- Tracking daily stock price movements to identify trends and potential entry/exit points
- Analyzing cryptocurrency volatility and price action over hourly or daily intervals
- Visualizing forex currency pair movements for technical analysis

## Data

- `date` (datetime) - The time period for each candlestick (e.g., day, hour)
- `open` (numeric) - Opening price at the start of the period
- `high` (numeric) - Highest price during the period
- `low` (numeric) - Lowest price during the period
- `close` (numeric) - Closing price at the end of the period
- Size: 20-100 periods for clear visualization
- Example: Daily OHLC prices for a stock over 30 trading days

## Notes

- Use green/red or blue/red color schemes for up/down days (green/red is most common)
- Ensure wicks are clearly visible but thinner than the candle body
- Time axis should have appropriate date formatting based on the data frequency
- Consider adding a subtle grid to help read price levels

## What a good version looks like

- A good version shows: one candle per period at its date, the body spanning open to close and the wick running from low to high through the middle of the body, all at their data values on the price axis, never displaced or smoothed.
- A good version shows: rising and falling periods told apart by one of the color pairs the Notes give, green or blue for a close above the open and red for a close below it, distinguishable in both themes.
- A good version shows: wicks clearly visible but thinner than the bodies, as the Notes ask, and bodies wide enough to read yet separated from their neighbors, so every period stays a distinct candle.
- A good version shows: a time axis whose date labels fit the data frequency, as the Notes ask, and a price axis that spans the lows and highs without being forced to zero.
- A good version shows: the basic variant's candles alone: besides the bodies and wicks and the subtle grid the Notes allow, no volume panel, moving averages or other indicator overlays, second instrument, trend, reference or mean lines, highlighted candles or bands, buy or sell signals, or callouts.
- Expected, not a defect: gaps at weekends and holidays or their deliberate removal, a body that collapses to a thin line when open and close are equal, candles with no wick on one or both sides, and bodies and wicks of very different lengths in volatile stretches.
