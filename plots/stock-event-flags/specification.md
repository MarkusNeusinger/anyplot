# stock-event-flags: Stock Chart with Event Flags

## Description

A stock price chart with flag-style markers annotating significant events such as earnings releases, dividends, stock splits, or news events. Unlike simple line annotations, flags are positioned above or below the price data with connector lines and styled icons that distinguish event types. This visualization is standard in financial trading platforms, enabling investors to correlate price movements with corporate actions and market events at a glance.

## Applications

- Annotating quarterly earnings announcements on equity price charts to analyze market reactions
- Marking dividend payment and ex-dividend dates on income-focused stock analysis
- Highlighting stock splits, reverse splits, or corporate restructuring events
- Visualizing the impact of news events, analyst upgrades/downgrades, or regulatory filings on price

## Data

- `date` (datetime) - Trading dates for the price series
- `open` (numeric) - Opening price at the start of each period (optional, for OHLC display)
- `high` (numeric) - Highest price during the period (optional, for OHLC display)
- `low` (numeric) - Lowest price during the period (optional, for OHLC display)
- `close` (numeric) - Closing price at the end of each period (required)
- `event_date` (datetime) - Dates of significant events to mark
- `event_type` (string) - Event category (e.g., earnings, dividend, split, news)
- `event_label` (string) - Short description displayed on the flag
- Size: 60-250 trading days with 3-15 events
- Example: Daily stock prices for a technology company over one year with quarterly earnings, dividends, and major product announcements marked

## Notes

- Flags should be positioned to avoid obscuring price data, using alternating heights or smart placement
- Use distinct icons or colors for different event types (e.g., dollar sign for dividends, chart icon for earnings)
- Include vertical dashed lines from flags to the price level for precise date alignment
- Hover or click interactions should reveal full event details where supported
- Consider using highlighted background regions for extended events (e.g., earnings blackout periods)
- Price can be displayed as a line chart or candlesticks depending on the library's capabilities

## What a good version looks like

- A good version shows: the price as a line of closes or as candlesticks, as the Notes allow, at its data values on every date, remaining the main series of the chart.
- A good version shows: every event as a flag at its event date, placed above or below the price so that it does not obscure the price data, by alternating heights or other placement, as the Notes ask, and clear of its neighboring flags.
- A good version shows: a vertical dashed line from each flag to the price level at its date, as the Notes ask, so the day an event belongs to can be read exactly.
- A good version shows: event types told apart by distinct icons or colors, as the Notes ask, and each flag carrying its short label, legible in both themes.
- A good version shows: highlighted background regions for extended events, if drawn as the Notes allow, spanning the dates of the event and staying behind the price and the flags.
- Expected, not a defect: flags unevenly spaced along the time axis and bunched where events fall close together, connector lines of different lengths, room above or below the price that only flags occupy, and price jumps at event dates.
