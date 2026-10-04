# ecdf-basic: Basic ECDF Plot

## Description

An ECDF (Empirical Cumulative Distribution Function) plot displays a step function that shows the proportion of observations less than or equal to each value. Unlike histograms, ECDF plots require no binning or smoothing, providing a non-parametric estimate of the cumulative distribution. The y-axis ranges from 0 to 1, allowing direct reading of percentiles and quantiles from the visualization.

## Applications

- Reading where a sample's spread, location and shape lie, as a base for comparing groups
- Identifying distribution characteristics such as median, quartiles, and percentiles at a glance
- Statistical analysis and hypothesis testing where the full distribution shape matters
- Visualizing sample distributions without making parametric assumptions about the underlying data

## Data

- `values` (numeric) - Continuous variable to visualize
- Size: 50-500 observations (works well from 10 to 10000+ but 50-500 is ideal for visualization)
- Example: Random samples from a normal distribution

## Notes

- The step function should increase by 1/n at each data point
- Y-axis must range from 0 to 1 representing cumulative proportion
- Consider using a distinct line style for clarity
- Grid lines help with reading specific percentile values

## What a good version looks like

- A good version shows: a single step function that rises only at the observed values and stays flat between them, never falling, with no binning and no smoothing of the steps.
- A good version shows: a step of 1/n at each data point, as the Notes ask, so the curve leaves 0 at the smallest observation and reaches 1 at the largest.
- A good version shows: a y axis that ranges from 0 to 1, as the Notes ask, labeled as cumulative proportion and shown in full.
- A good version shows: the basic variant's single step line, in the distinct line style and with the grid lines the Notes allow, and no second sample, fitted or theoretical curve, confidence band, median, quartile or other reference lines, highlighted points or bands, or callouts.
- Expected, not a defect: visible stair steps, taller jumps where values are tied, long flat runs in sparse regions and the tails, and a steep rise where observations crowd; none of them is to be smoothed.
