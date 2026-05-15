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
