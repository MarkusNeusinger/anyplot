# line-markers: Line Plot with Markers

## Description

A line plot with visible markers at each data point, combining line and scatter plot features. This is particularly useful for sparse data where individual observations are significant.

## Applications

- Sparse datasets where each point matters
- Highlighting specific data points on trend lines
- Experimental data with discrete measurements
- Quality control charts with individual readings

## Data

- `x` (continuous, numeric) - X-axis values
- `y` (numeric, continuous) - Y-axis values; supports multiple series

Size: 10–1000 points per series recommended

Example:
```
x    | y
-----|-----
0    | 10.5
1    | 12.3
2    | 11.8
3    | 14.2
```

## Notes

- Markers should be clearly visible against the line
- Use different marker shapes for multiple series
- Marker size should be proportional to line thickness
- Consider filled vs unfilled markers for distinction

## What a good version looks like

- A good version shows: a line joining the values in x order with a marker on every data point, each marker centered on its (x, y) value and never nudged aside to separate it from a neighbor.
- A good version shows: markers that stand out against their line, as the Notes ask, sized in proportion to the line's thickness so that neither the line nor the markers dominate.
- A good version shows: where there are several series, a different marker shape for each, as the Notes ask, so the series can be told apart by shape as well as by color; filled and unfilled markers, if used, add to that distinction.
- A good version shows: markers that stay separate symbols along the line; where the points are dense, smaller markers keep them from merging into one thick band.
- Expected, not a defect: markers that touch or cover each other where series cross or two values coincide, uneven spacing between points, and short-term noise in the series.
