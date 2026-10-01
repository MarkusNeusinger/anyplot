# indicator-bollinger: Bollinger Bands Indicator Chart

## Description

A Bollinger Bands chart displays price data with a volatility envelope consisting of three lines: a middle band (simple moving average), an upper band (SMA plus 2 standard deviations), and a lower band (SMA minus 2 standard deviations). This technical indicator helps traders identify overbought/oversold conditions, volatility patterns, and potential price breakouts by showing how prices relate to their recent statistical range.

## Applications

- Identifying overbought conditions when price touches the upper band in stock trading
- Detecting oversold opportunities when price approaches the lower band in cryptocurrency analysis
- Measuring market volatility by observing band width expansion and contraction
- Spotting potential trend reversals when prices break outside the bands

## Data

- `date` (datetime) - Trading date or timestamp for each period
- `close` (numeric) - Closing price for each period
- `sma` (numeric) - Simple moving average (middle band), typically 20-period
- `upper_band` (numeric) - Upper band value (SMA + 2 standard deviations)
- `lower_band` (numeric) - Lower band value (SMA - 2 standard deviations)
- Size: 60-200 periods for meaningful pattern visualization
- Example: Daily stock prices with 20-day SMA and 2 standard deviation bands over 120 trading days

## Notes

- Display the price line (close) prominently, typically as a line or candlestick
- Upper and lower bands should use the same color with semi-transparent fill between them
- Middle band (SMA) should be clearly visible, often as a dashed or dotted line
- Standard parameters are 20-period SMA with 2 standard deviations, note in chart if different
- Consider showing band width as a secondary indicator or noting squeeze patterns

## What a good version looks like

- A good version shows: the price drawn prominently as a line or as candlesticks, as the Notes ask, with the three bands overlaid on the same price axis, every line at its computed value on every date.
- A good version shows: the upper and lower bands in one shared color with a semi-transparent fill between them, as the Notes ask, so the price and the middle band stay visible through the fill in both themes.
- A good version shows: a middle band that is clearly visible, as the Notes ask, running midway between the upper and lower bands and told apart from the price, for instance by a dashed or dotted stroke.
- A good version shows: the period and the standard deviation multiple noted in the chart when they differ from the standard parameters, as the Notes ask.
- A good version shows: a band width panel or a squeeze annotation, if drawn as the Notes allow, that agrees with where the bands actually narrow and leaves the price and bands uncovered.
- Expected, not a defect: bands that narrow in quiet stretches and widen in volatile ones, a price that touches, rides or briefly pierces a band, bands that lag sharp moves, and bands that begin only where a full averaging period is available.
