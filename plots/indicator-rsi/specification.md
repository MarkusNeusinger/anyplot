# indicator-rsi: RSI Technical Indicator Chart

## Description

A Relative Strength Index (RSI) chart displaying the momentum oscillator on a 0-100 scale with horizontal threshold lines at 70 (overbought) and 30 (oversold). The RSI measures the speed and magnitude of recent price changes to evaluate overbought or oversold conditions. This is a fundamental momentum indicator in technical analysis, helping traders identify potential reversal points when the market reaches extreme conditions.

## Applications

- Identifying overbought conditions in stocks when RSI exceeds 70, signaling potential sell opportunities
- Detecting oversold conditions in cryptocurrency markets when RSI drops below 30, indicating potential buying points
- Confirming trend strength and momentum by observing RSI behavior relative to thresholds

## Data

- `date` (datetime) - Trading date or timestamp for each period
- `rsi` (numeric) - RSI value between 0 and 100
- Size: 60-200 periods for meaningful pattern recognition
- Example: Daily RSI values calculated from stock closing prices over 120 trading days using 14-period lookback

## Notes

- Y-axis must be fixed from 0 to 100
- Include horizontal reference lines at 30 (oversold) and 70 (overbought)
- Optionally include a centerline at 50 to show bullish/bearish bias
- RSI line should be clearly visible, typically in a distinct color (e.g., purple or blue)
- Shade or highlight the overbought zone (70-100) and oversold zone (0-30) for visual clarity
- Standard lookback period is 14, but should be noted in the chart
- Typically shown as a separate panel below a price chart, but can stand alone

## What a good version looks like

- A good version shows: the RSI as one continuous line at its computed values, clearly visible as the Notes ask, in a color that stands out from the reference lines and the shaded zones, on a y-axis fixed from 0 to 100, as the Notes require.
- A good version shows: horizontal reference lines at 30 and 70, as the Notes ask, readable as the oversold and overbought levels, and the centerline at 50 the Notes allow, if drawn, all subordinate to the RSI line and visible in both themes.
- A good version shows: the overbought zone above 70 and the oversold zone below 30 shaded or highlighted, as the Notes ask, lightly enough that the RSI line stays visible inside them in both themes.
- A good version shows: the lookback period noted in the chart, as the Notes ask.
- A good version shows: a price panel above the RSI panel, if drawn as the Notes allow, sharing its date axis while the RSI panel keeps its own fixed scale.
- Expected, not a defect: empty space near 0 and 100 that the line rarely reaches, long runs above 70 or below 30 in a strong trend, a jagged line that spends most of its time between the two levels, and a line that begins only once the lookback is filled.
