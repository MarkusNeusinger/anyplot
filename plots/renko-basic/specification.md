# renko-basic: Basic Renko Chart

## Description

A Renko chart displays price movements using fixed-size bricks that ignore time and focus purely on price action. A new brick is drawn only when the price moves by a specified amount (brick size), filtering out market noise and minor fluctuations. Bullish bricks (price increase) and bearish bricks (price decrease) alternate direction on trend reversals, making it easy to identify trends, support/resistance levels, and potential trading signals.

## Applications

- Identifying clear trend directions in stock prices by filtering out intraday noise and focusing on significant price movements
- Spotting support and resistance levels in forex trading where price repeatedly reverses at certain brick levels
- Generating cleaner trading signals by removing time-based volatility from cryptocurrency price analysis

## Data

- `date` (datetime) - The timestamp when each price point was recorded
- `close` (numeric) - Closing price or last traded price at each timestamp
- Brick size: A fixed price amount that determines when a new brick is drawn (e.g., $1, $5, or percentage-based)
- Size: 100-500 price observations to generate 20-50 meaningful bricks
- Example: Daily closing prices for a stock over 6 months with a $2 brick size

## Notes

- Use green/up color for bullish bricks and red/down color for bearish bricks
- Bricks should be uniform in size and clearly separated with a small gap
- X-axis can show brick index or estimated date ranges (since time is irregular)
- Consider adding a subtle grid to help identify price levels
- The brick size significantly affects the chart appearance - smaller bricks show more detail, larger bricks show broader trends

## What a good version looks like

- A good version shows: bricks uniform in size and clearly separated by a small gap, as the Notes ask, each spanning exactly one brick size on the price axis.
- A good version shows: every brick in its own column one step to the right of the last and one brick higher or lower than it, so runs of bricks read as diagonal staircases and no two bricks share a column.
- A good version shows: bullish bricks in green and bearish bricks in red, as the Notes ask, distinguishable in both themes.
- A good version shows: a horizontal position that is construction, not time: one even column per brick, on an x-axis that shows the brick index or the estimated date ranges the Notes allow.
- A good version shows: the basic variant's bricks alone: besides the bricks and the subtle grid the Notes allow, no underlying price line or candles, wicks, volume panel, moving averages, trend, reference or mean lines, highlighted bricks or bands, buy or sell signals, or callouts.
- Expected, not a defect: no regular time axis, date labels that are unevenly spaced when dates are shown, far fewer bricks than price observations, long staircases in one color, and price levels revisited by several columns.
