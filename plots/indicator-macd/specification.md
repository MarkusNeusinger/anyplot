# indicator-macd: MACD Technical Indicator Chart

## Description

A MACD (Moving Average Convergence Divergence) chart displaying three components: the MACD line, signal line, and histogram. The MACD line represents the difference between 12-day and 26-day exponential moving averages, while the signal line is a 9-day EMA of the MACD. The histogram visualizes the difference between these two lines. This is an essential momentum oscillator for technical analysis, helping traders identify trend direction, momentum strength, and potential buy/sell signals through line crossovers.

## Applications

- Analyzing stock price momentum to identify trend reversals and entry/exit points
- Generating trading signals for cryptocurrency markets based on MACD/signal line crossovers
- Confirming trend strength by observing histogram expansion or contraction

## Data

- `date` (datetime) - Trading date or timestamp for each period
- `macd` (numeric) - MACD line value (12-day EMA minus 26-day EMA)
- `signal` (numeric) - Signal line value (9-day EMA of MACD)
- `histogram` (numeric) - Difference between MACD and signal line
- Size: 60-200 periods for meaningful pattern recognition
- Example: Daily MACD values calculated from stock closing prices over 120 trading days

## Notes

- Display histogram as bars with green (positive) and red (negative) colors
- Include a zero reference line to highlight crossover signals
- MACD and signal lines should use distinct colors (e.g., blue and orange)
- Standard parameters are 12, 26, 9 but should be noted in the chart
- Typically shown as a separate panel below a price chart, but can stand alone

## What a good version looks like

- A good version shows: the MACD line and the signal line as two continuous lines in distinct colors, as the Notes ask, each at its computed value on every date and identified so a reader can tell which is which.
- A good version shows: the histogram as bars reaching from zero to the difference between the MACD and signal lines, green when positive and red when negative, as the Notes ask, changing sign exactly where the two lines cross.
- A good version shows: a zero reference line, as the Notes ask, visible in both themes, on an axis that covers the positive and negative values around it, with the lines readable over the histogram bars.
- A good version shows: the parameters noted in the chart, as the Notes ask.
- A good version shows: a price panel above the MACD panel, if drawn as the Notes allow, sharing its date axis while the MACD panel keeps its own scale around zero.
- Expected, not a defect: an oscillator with no fixed bounds whose axis is not symmetric around zero, turns that lag the price, histogram bars much shorter than the swings of the lines, many shallow crossovers in sideways stretches, and lines that begin only once the averages are filled.
