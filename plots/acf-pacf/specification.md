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
