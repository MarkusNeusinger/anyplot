# line-styled: Styled Line Plot

## Description

A line plot using different line styles (solid, dashed, dotted, dash-dot) to distinguish multiple data series. This is especially useful for black-and-white printing or when color distinction is insufficient.

## Applications

- Comparing trends in print publications
- Distinguishing overlapping lines without color
- Accessibility-friendly visualizations
- Technical documentation with monochrome printing

## Data

- `x` (continuous) - Time or sequence variable for the horizontal axis
- `y_1`, `y_2`, ... (numeric) - Multiple series to distinguish with different line styles
- Size: 50-500 points recommended (sufficient to show trends and line style clarity)
- Example: Time series data with 3-5 series for optimal line style distinction

Example structure:
```
x    | Series A | Series B | Series C
-----|----------|----------|----------
0    | 10       | 15       | 12
1    | 12       | 14       | 15
2    | 15       | 13       | 18
...
```

## Notes

- Standard styles: solid, dashed, dotted, dash-dot
- Include legend mapping styles to series names
- Line width should be consistent across styles
- Consider line style visibility at different scales

## What a good version looks like

- A good version shows: every series as a line joining its values in x order, each in its own line style, drawing first on the standard styles the Notes list: solid, dashed, dotted and dash-dot.
- A good version shows: series that can be told apart by line style alone, so the chart still works in monochrome; color, if used, comes on top of the style difference and does not replace it.
- A good version shows: dash and dot patterns that stay recognizable along the whole line: dots read as dots and dashes as dashes, rather than merging into a solid line or breaking into scattered specks.
- A good version shows: one line width across all styles, as the Notes ask, so that no series looks heavier only because of its pattern.
- A good version shows: a legend mapping each style to its series name, as the Notes ask, with swatches long enough to show the full pattern.
- Expected, not a defect: lines that cross or run close together, the gaps of a dashed or dotted line falling on a peak or a crossing, and short-term noise in the series.
