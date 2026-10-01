# histogram-cumulative: Cumulative Histogram

## Description

A cumulative histogram (also known as an ogive or cumulative frequency histogram) displays the running total of observations up to each bin boundary. The y-axis shows cumulative count or proportion, creating a monotonically increasing step function that reaches the total sample size (or 1.0 for normalized).

## Applications

- Visualizing percentiles and quantile positions
- Understanding data distribution thresholds (e.g., "what percentage is below X?")
- Quality control and process analysis
- Comparing empirical vs theoretical CDFs
- Financial risk analysis (Value at Risk)

## Data

The visualization requires:
- **Numeric variable**: Continuous values to bin and accumulate

Example structure:
```
Value
------
12.5
18.3
15.7
22.1
...
```

## Notes

- Y-axis shows cumulative count or proportion (0 to n, or 0 to 1)
- The curve is always monotonically non-decreasing
- Often displayed as steps (not smooth curves) to show discrete bins
- Can use `density=True` or `cumulative=True` parameters
- Useful for determining what proportion of data falls below any threshold

## What a good version looks like

- A good version shows: one level per bin over contiguous bins, each at the running total of observations up to that bin's upper edge, so no level is ever lower than the one before it.
- A good version shows: a y axis that starts at zero, is labeled as cumulative count or cumulative proportion, and is reached in full at the last bin: the total sample size on a count axis, or 1 on a proportion axis.
- A good version shows: the discrete bins still readable in the shape, usually as steps or adjacent bars as the Notes describe, with any overlaid reference curve, if drawn, distinguishable from the binned data.
- Expected, not a defect: flat runs across empty bins, a steep rise through the middle of the data, a flattening toward the top and the tallest levels crowded at the right end; the one-sided rise is the point of the chart.
