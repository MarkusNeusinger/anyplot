# acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot

## Description

Displays the autocorrelation function (ACF) and partial autocorrelation function (PACF) of a time series as vertical stem/bar plots arranged in two vertically stacked subplots. Each lag is represented by a vertical line from zero to the correlation value, with horizontal dashed lines indicating 95% confidence bounds. These plots are essential for identifying the order of AR and MA components in ARIMA modeling and for diagnosing residual independence.

## Applications

- Identifying appropriate ARIMA(p,d,q) model orders from the decay patterns in ACF and PACF before fitting a time series model
- Diagnosing model residuals to verify that no significant autocorrelation remains after fitting a forecasting model
- Detecting seasonal patterns in economic or climate data by observing periodic spikes at seasonal lags

## Data

- `value` (float) - Time series observations in chronological order
- `timestamp` (datetime, optional) - Time index for the series; equally spaced intervals assumed
- Size: 100-500 observations recommended for reliable correlation estimates
- Example: Monthly airline passenger counts, daily stock returns, or hourly temperature readings

## Notes

- Display ACF in the top subplot and PACF in the bottom subplot, sharing the x-axis (lag number)
- Use vertical stem lines (not filled bars) from the zero baseline to each correlation value
- Show 95% confidence interval as horizontal dashed lines at approximately +/-1.96/sqrt(N)
- Include lag 0 in ACF (always 1.0) but start PACF from lag 1
- Label x-axis as "Lag" and y-axes as "ACF" and "PACF" respectively
- Use 30-40 lags by default, adjusting based on data length

## What a good version looks like

- A good version shows: the ACF in the top panel and the PACF in the bottom panel, as the Notes ask, sharing one lag axis so each lag lines up vertically across the two, with the x axis labeled Lag and the y axes ACF and PACF.
- A good version shows: one thin vertical stem per lag from the zero baseline to its correlation value, not a filled bar, as the Notes ask, every stem at its own lag and ending at its computed value.
- A good version shows: horizontal dashed lines at the upper and lower confidence bounds, as the Notes ask, the same distance above and below zero, running across all lags and visible in both themes.
- A good version shows: the ACF including lag 0, where its value is 1.0, and the PACF starting at lag 1, as the Notes ask, with y axes that leave room for negative correlations and the lower bound.
- Expected, not a defect: a lag 0 stem that towers over the rest, an ACF that decays slowly or oscillates with many stems outside the bounds, a PACF that drops inside the bounds after a few lags, spikes at seasonal lags, an occasional stem just outside the bounds by chance, and mostly short stems.
