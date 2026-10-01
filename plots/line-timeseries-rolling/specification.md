# line-timeseries-rolling: Time Series with Rolling Average Overlay

## Description

A time series plot that displays raw data points alongside a smoothed rolling average (moving average) line. The raw data shows actual observations while the rolling average reveals underlying trends by reducing noise and short-term fluctuations. This dual-layer visualization is essential for trend identification, making patterns visible that might be obscured by day-to-day volatility.

## Applications

- Analyzing stock price movements with a moving average to identify buy/sell signals and trend reversals
- Monitoring website traffic or user engagement metrics with smoothed trends for seasonal pattern detection
- Tracking sensor data (temperature, humidity) with noise reduction to reveal true environmental trends

## Data

- `date` (datetime) - Timestamp values representing points in time
- `value` (numeric) - Raw measurements or observations at each timestamp
- `rolling_avg` (numeric) - Computed rolling average (e.g., 7-day, 30-day window)
- Size: 50-500 points (enough data for meaningful rolling window calculation)
- Example: Daily stock closing prices with 20-day moving average, hourly temperature readings with 24-hour rolling mean

## Notes

- Use a lighter, semi-transparent style for raw data (thin line or markers with alpha)
- Display the rolling average as a prominent, smooth line in a contrasting color
- Include a legend clearly distinguishing "Raw Data" from "Rolling Average (N-day)"
- Consider showing the window size in the legend or title (e.g., "7-Day Rolling Average")
- Grid lines on both axes improve readability of underlying values
- The rolling average line will be shorter than raw data due to window requirements

## What a good version looks like

- A good version shows: the raw observations at their data values on a date axis, as a thin line or markers in a lighter, semi-transparent style, as the Notes ask, receding behind the rolling average yet still visible in both themes.
- A good version shows: the rolling average as the most prominent mark, a smooth line in a color that contrasts with the raw data and tracks its level rather than drifting away from it.
- A good version shows: the rolling average beginning only once its window is filled, so it covers a shorter span than the raw data instead of being padded back to the first date.
- A good version shows: a legend distinguishing the raw data from the rolling average, as the Notes ask, with the window size named in the legend or title if it is shown.
- A good version shows: grid lines on both axes, subordinate to both series, so the underlying values can be read off.
- Expected, not a defect: raw data that is noisy and spiky around the average, a rolling average that lags turning points and flattens short peaks and troughs, and a rolling line that is shorter than the raw series.
