# errorbar-asymmetric: Asymmetric Error Bars Plot

## Description

An asymmetric error bar plot displays data points with separate upper and lower error magnitudes, allowing different-sized bars extending above and below each point. This visualization is essential for representing skewed distributions, non-symmetric confidence intervals, or data where uncertainty differs in positive and negative directions. Common applications include percentile-based intervals, log-transformed data, and Bayesian credible intervals.

## Applications

- Scientific research presenting results with non-symmetric confidence intervals (e.g., 5th-95th percentile)
- Financial forecasting showing different upside and downside risk projections
- Clinical trials displaying treatment effects with asymmetric uncertainty bounds
- Environmental monitoring reporting measurements with different detection limits above and below

## Data

- `x` (categorical or numeric) - Categories or positions on the x-axis
- `y` (numeric) - Central values representing mean, median, or point estimates
- `error_lower` (numeric) - Error magnitude extending below each point
- `error_upper` (numeric) - Error magnitude extending above each point
- Size: 3-20 data points for clarity

## Notes

- Error bars should have visible caps (horizontal lines at ends) to clearly mark the error range
- Consider using different colors or markers when comparing multiple series
- Include a legend or annotation explaining what the asymmetric bounds represent (e.g., "10th-90th percentile", "95% CI")
- Useful for log-scale axes where symmetric intervals would appear asymmetric after transformation

## What a good version looks like

- A good version shows: one marker per data point at its central value, with one arm reaching to the lower bound and one to the upper bound, each arm's length set by its own error value, on a value axis that spans every error bar, and no point re-centered within its interval.
- A good version shows: visible caps at both ends of every error bar, as the Notes ask, and a marker distinct from the bar, so where the central value sits between the two arms is unmistakable in both themes.
- A good version shows: a legend or annotation stating what the bounds represent, as the Notes ask, such as a percentile range or a confidence interval.
- A good version shows: several series, if compared, told apart by color or marker as the Notes suggest, each keeping one color and marker throughout and named in a legend.
- Expected, not a defect: arms of unequal length, in ratios that differ from point to point, a point sitting close to one end of its interval, some intervals that are nearly symmetric, and intervals of neighboring points that overlap.
