# histogram-returns-distribution: Returns Distribution Histogram

## Description

A histogram showing the distribution of financial returns (daily, weekly, or monthly) with a normal distribution overlay for comparison. This visualization is essential for risk analysis, allowing analysts to assess whether returns follow a normal distribution, identify fat tails indicating higher-than-expected extreme events, and measure asymmetry through skewness. Key statistics are displayed directly on the plot for quick interpretation.

## Applications

- Risk analysis and return distribution assessment for portfolio management
- Comparing actual return distributions to theoretical normal distribution assumptions
- Identifying fat tails and skewness in financial time series for VaR calculations
- Evaluating portfolio return characteristics and risk metrics

## Data

- `date` (datetime) - Period dates for the returns
- `returns` (numeric) - Percentage returns (daily, weekly, or monthly)
- Size: 252+ observations recommended (1 year of daily data)
- Example: Daily stock returns, ETF returns, or portfolio returns

## Notes

- Show percentage returns on x-axis with clear labels
- Overlay normal distribution curve fitted to the data for comparison
- Display key statistics in a text box: mean, standard deviation, skewness, kurtosis
- Highlight tail regions beyond 2 standard deviations with distinct coloring
- Use appropriate bin width for return data (typically 20-50 bins for 252+ observations)
- Consider using density normalization so histogram and normal curve are on comparable scales

## What a good version looks like

- A good version shows: a histogram of the returns as contiguous bars over equal-width bins, on an x axis labeled as percentage returns, as the Notes ask.
- A good version shows: a normal curve fitted to the returns' mean and standard deviation, drawn over the bars on a comparable scale (the density normalization the Notes suggest, or an equivalent), so bars and curve compare directly.
- A good version shows: the tail regions beyond 2 standard deviations on both sides of the mean in a distinct coloring, as the Notes ask, with the boundary between the central and the tail coloring at those two values, or at the nearest bin edge where whole bars are colored.
- A good version shows: a text box with the mean, standard deviation, skewness and kurtosis, as the Notes ask, placed where it covers neither the bars nor the curve.
- Expected, not a defect: a central peak taller and narrower than the normal curve, tail bars that rise above it, a lopsided shape, and isolated extreme bars separated by empty bins; fat tails and skew are what the chart exists to show.
