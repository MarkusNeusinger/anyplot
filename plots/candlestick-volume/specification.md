# candlestick-volume: Stock Candlestick Chart with Volume

## Description

A professional candlestick chart combining OHLC (open, high, low, close) price data with volume bars in a synchronized lower pane. The dual-pane layout presents price action in the main chart with corresponding trading volume below, sharing a common time axis. This format is the standard for technical analysis platforms, enabling traders to correlate price movements with trading activity and identify volume-confirmed trends or reversals.

## Applications

- Analyzing stock price movements alongside trading volume to confirm breakout patterns
- Identifying divergences between price trends and volume for potential reversal signals
- Evaluating cryptocurrency or forex pairs with volume context for entry/exit decisions

## Data

- `date` (datetime) - Trading date or timestamp for each period
- `open` (numeric) - Opening price at the start of the period
- `high` (numeric) - Highest price during the period
- `low` (numeric) - Lowest price during the period
- `close` (numeric) - Closing price at the end of the period
- `volume` (numeric) - Number of shares or units traded during the period
- Size: 30-120 periods for clear visualization without overcrowding
- Example: Daily OHLC data with volume for a stock over 60 trading days

## Notes

- Use a shared x-axis between the candlestick and volume panes with proper date formatting
- Volume bars should use the same up/down color scheme as candlesticks for visual consistency
- The price pane should occupy roughly 70-75% of the vertical space, volume pane 25-30%
- Where the library supports interaction, include a crosshair or cursor that spans both panes for precise price/volume reading
- Grid lines should be subtle and aligned across both panes

## What a good version looks like

- A good version shows: in the upper pane one candle per period, the body spanning open to close and the wick running from low to high, at their data values on the price axis, with up and down candles distinguishable in both themes.
- A good version shows: in the lower pane one volume bar per period rising from a zero baseline to that period's volume, on the x-axis shared with the price pane, as the Notes ask, so every bar sits directly beneath its candle.
- A good version shows: volume bars in the same up and down colors as their candles, as the Notes ask, so a bar's color always agrees with the candle above it.
- A good version shows: the two panes stacked in roughly the proportions the Notes give, the price pane much the taller, with date labels on the shared axis in a format that fits the data frequency.
- A good version shows: subtle grid lines aligned across both panes, as the Notes ask, and the crosshair or cursor the Notes ask for, where the output draws one, as a single vertical guide running through both panes at one date.
- Expected, not a defect: gaps at weekends and holidays or their deliberate removal, a few volume spikes that leave most bars short, a price axis that does not start at zero above a volume axis that does, and candles whose body collapses to a line.
