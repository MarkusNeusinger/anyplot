# line-multi: Multi-Line Comparison Plot

## Description

A multi-line plot displays multiple data series on the same axes for direct comparison. Each series is represented by a distinct line with its own color and optional style, making it easy to identify trends, correlations, and divergences between variables. This visualization is essential for comparing related metrics over a common sequence or time period.

## Applications

- Comparing stock prices or financial metrics of multiple companies over trading days
- Tracking performance metrics of different products or campaigns over time
- Analyzing temperature or weather patterns across multiple cities or regions

## Data

- `x` (numeric/datetime) - Shared sequential or time values for alignment
- `y1, y2, ...` (numeric) - Multiple continuous series to compare
- `series` (categorical) - Optional grouping variable if data is in long format
- Size: 10-200 points per series, 2-6 series recommended
- Example: Monthly sales for 3 product lines, daily stock prices for 4 companies

## Notes

- Use distinct colors for each line to ensure clear differentiation
- Include a legend that clearly identifies each series
- Consider varying line styles (solid, dashed, dotted) for additional distinction
- Optional markers at data points can improve readability for sparse data
- Keep the number of series manageable (2-6) to avoid visual clutter

## What a good version looks like

- A good version shows: every series as its own line on one shared pair of axes, each joining its values in x order, so levels, trends and divergences compare directly.
- A good version shows: a distinct color per line, as the Notes ask, the same along the whole line and distinguishable from every other line in both themes.
- A good version shows: a legend that names every series, as the Notes ask, with swatches that match each line's color and, where used, its line style and marker.
- A good version shows: varied line styles and markers at the data points, if used, as an addition to color: each series keeps one style throughout, and markers stay small enough that the lines still read as lines.
- A good version shows: a manageable handful of series, as the Notes ask, so that each line can be followed from end to end.
- Expected, not a defect: lines that cross, run close together or coincide at some points, and series with very different levels or volatility; those are the comparison the chart exists to show.
