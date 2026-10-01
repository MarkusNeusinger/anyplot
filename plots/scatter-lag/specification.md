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

## What a good version looks like

- A good version shows: one point per pair of observations a fixed lag apart, the earlier value on the x axis and the later one on the y axis, with axis labels or a title that state the lag order.
- A good version shows: both axes covering the same value range, because they show the same variable, so the y = x reference line the Notes ask for runs along the plot's diagonal, drawn lighter than the points.
- A good version shows: points left unconnected and translucent enough that the dense center of a long series remains readable, with none jittered off its values.
- A good version shows: the time-index coloring, if used as the Notes allow, on a sequential colormap with a color bar labeled as time or observation index, and the correlation coefficient, if annotated, placed clear of the points.
- Expected, not a defect: a round, structureless cloud for an uncorrelated series, a tight band along the diagonal for a strongly autocorrelated one, and a few points far from the rest; the shape is the diagnosis.
