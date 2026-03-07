# indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart

## Description

Displays the Ichimoku Kinko Hyo ("one glance equilibrium chart") overlay on a candlestick price chart. The indicator plots five lines — Tenkan-sen (conversion), Kijun-sen (base), Senkou Span A, Senkou Span B, and Chikou Span (lagging) — with the area between Senkou Span A and B filled as the "Kumo" (cloud). The cloud color changes depending on which span is on top, providing an at-a-glance view of trend direction, momentum, and support/resistance zones.

## Applications

- Equity or forex traders identifying trend direction and momentum using the cloud color and thickness
- Technical analysts locating dynamic support and resistance zones formed by the Kumo
- Swing traders spotting bullish/bearish crossover signals between Tenkan-sen and Kijun-sen

## Data

- `date` (datetime) - Trading date or timestamp
- `open` (float) - Opening price
- `high` (float) - Highest price in the period
- `low` (float) - Lowest price in the period
- `close` (float) - Closing price
- `tenkan_sen` (float) - Conversion line: (9-period high + 9-period low) / 2
- `kijun_sen` (float) - Base line: (26-period high + 26-period low) / 2
- `senkou_span_a` (float) - Leading Span A: (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
- `senkou_span_b` (float) - Leading Span B: (52-period high + 52-period low) / 2, plotted 26 periods ahead
- `chikou_span` (float) - Lagging Span: current close plotted 26 periods behind
- Size: 120-300 trading periods (to allow the 52-period lookback plus visible history)
- Example: Daily OHLC stock data with pre-computed Ichimoku components

## Notes

- The cloud (Kumo) should be filled between Senkou Span A and Senkou Span B, with a green/bullish tint when Span A > Span B and a red/bearish tint when Span B > Span A
- Tenkan-sen and Kijun-sen should be drawn as distinct colored lines over the candlestick chart
- Chikou Span should be plotted shifted 26 periods into the past
- Senkou Span A and B should be plotted shifted 26 periods into the future
- Use standard Ichimoku parameters (9, 26, 52) for computing the indicator values in generated sample data
- Candlesticks should use conventional green (up) and red (down) coloring
