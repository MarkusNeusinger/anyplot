# ohlc-bar: OHLC Bar Chart

## Description

An OHLC (Open-High-Low-Close) bar chart displays financial price data using vertical bars with horizontal tick marks. Each bar shows the price range from high to low as a thin vertical line, with a left tick indicating the opening price and a right tick indicating the closing price. Unlike candlestick charts that use colored bodies, OHLC bars provide a cleaner, less cluttered view favored by technical analysts who prefer to focus on price levels rather than visual patterns.

## Applications

- Analyzing daily stock price movements with focus on precise price levels
- Comparing price action across multiple securities on the same chart without color distraction
- Technical analysis where traders prefer bar charts over candlesticks for pattern recognition

## Data

- `date` (datetime) - The time period for each bar (e.g., day, hour, minute)
- `open` (numeric) - Opening price at the start of the period
- `high` (numeric) - Highest price during the period
- `low` (numeric) - Lowest price during the period
- `close` (numeric) - Closing price at the end of the period
- Size: 20-100 periods for clear visualization
- Example: Daily OHLC prices for a stock over 30-60 trading days

## Notes

- Use thin vertical lines for the high-low range
- Horizontal ticks should extend to the left for open and right for close
- Consider using different colors for up bars (close > open) vs down bars (close < open) for easier reading
- Time axis should have appropriate date formatting based on data frequency
- Grid lines help read exact price levels

## What a good version looks like

- A good version shows: one bar per period at its date: a thin vertical line from the low to the high, with a short horizontal tick to the left at the open and one to the right at the close, as the Notes ask, all at their data values on the price axis.
- A good version shows: ticks long enough to tell left from right at a glance, yet short enough that they do not touch the ticks of the neighboring bars, so every period stays a separate bar.
- A good version shows: up bars and down bars in different colors, if colored by direction as the Notes allow, distinguishable in both themes; with a single color the direction still reads from the two ticks.
- A good version shows: a time axis whose date labels fit the data frequency, as the Notes ask, a price axis that spans the lows and highs without being forced to zero, and grid lines, if drawn, that stay behind the bars.
- Expected, not a defect: no filled bodies, gaps at weekends and holidays or their deliberate removal, open and close ticks at the same level, a tick sitting at the very end of its line when the open or close is the high or low, and bars of very different lengths.
