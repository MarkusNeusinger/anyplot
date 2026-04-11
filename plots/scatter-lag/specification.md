# scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis

## Description

A lag plot is a scatter plot of a time series against a lagged version of itself, plotting y(t) on the x-axis versus y(t+k) on the y-axis for a given lag order k. If the data is purely random, points scatter uniformly with no visible structure; if autocorrelation is present, distinctive patterns emerge — linear clusters for autoregressive processes, elliptical shapes for seasonal data. This provides a quick visual diagnostic for time series dependence, complementing numerical tools like ACF/PACF.

## Applications

- Checking for autocorrelation before applying regression models that assume independent residuals
- Diagnosing stationarity and serial dependence in financial return series
- Identifying seasonal or cyclical patterns in sensor and environmental monitoring data
- Validating residual independence after fitting ARIMA or other time series models

## Data

- `value` (float) — time series observations in chronological order
- `lag` (int) — lag order k, default 1 (plot y(t) vs y(t+k))
- Size: 100–5000 observations
- Example: daily stock returns, hourly temperature readings, or synthetic AR(1) process data

## Notes

- Default lag = 1, but the implementation should support configurable lag values (e.g., 1, 7, 12)
- Include a diagonal reference line (y = x) to help assess whether the series is uncorrelated
- Optionally color points by their time index to reveal temporal structure within the scatter
- Strong linear pattern along the diagonal indicates high positive autocorrelation at the given lag; perpendicular spread indicates negative autocorrelation
- Consider adding a correlation coefficient annotation (r value) to quantify the visual pattern
