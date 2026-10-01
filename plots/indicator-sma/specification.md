# indicator-sma: Simple Moving Average (SMA) Indicator Chart

## Description

A Simple Moving Average (SMA) chart displays price or value data with one or more SMA overlays, typically showing short, medium, and long-term periods (e.g., 20, 50, 200-day). Each SMA line smooths out price fluctuations by averaging the last N data points, revealing underlying trends at different time scales. This multi-period overlay is fundamental to technical analysis, helping traders identify trend direction, support/resistance levels, and potential crossover signals.

## Applications

- Identifying trend direction by comparing price position relative to 50-day and 200-day SMAs in stock analysis
- Detecting golden cross (50-day crosses above 200-day) and death cross signals in cryptocurrency trading
- Analyzing short-term momentum versus long-term trend using 20/50/200-day SMA combinations
- Smoothing noisy time series data to reveal underlying patterns in sensor or metrics monitoring

## Data

- `date` (datetime) - Trading date or timestamp for each period
- `close` (numeric) - Closing price or value for each period
- `sma_short` (numeric) - Short-term SMA (e.g., 20-period)
- `sma_medium` (numeric) - Medium-term SMA (e.g., 50-period)
- `sma_long` (numeric) - Long-term SMA (e.g., 200-period)
- Size: 250-500 periods to show meaningful long-term SMA behavior
- Example: Daily stock closing prices with 20, 50, and 200-day SMAs over one year of trading

## Notes

- Display the price/close line prominently, typically as a solid line or with subtle markers
- Each SMA should use a distinct color with consistent styling across all implementations
- Include a legend showing the period for each SMA (e.g., "SMA 20", "SMA 50", "SMA 200")
- Longer SMAs will have more initial null values due to the calculation window
- Standard periods are 20/50/200 for daily data, but other combinations like 10/20/50 are also common
- Grid lines on the y-axis improve price level readability

## What a good version looks like

- A good version shows: the close drawn prominently, as the Notes ask, with every SMA overlaid on the same axis at its computed value on every date where it is defined, so the price stays the dominant series.
- A good version shows: a distinct color for each SMA, as the Notes ask, so the SMAs can be told apart from one another and from the price in both themes.
- A good version shows: a legend that gives the period of each SMA, as the Notes ask.
- A good version shows: each SMA beginning only where its window is full, so the longer SMAs start later, as the Notes describe, never back-filled, joined to the axis or drawn from zero.
- A good version shows: SMAs that behave like their periods: the short one follows the price closely, the long one is the smoothest and slowest to turn, and each runs through the middle of the prices it averages.
- Expected, not a defect: SMAs that lag the price, an empty warm-up stretch that leaves the longest SMA covering only part of the window, and lines that run close together and cross repeatedly in sideways stretches.
