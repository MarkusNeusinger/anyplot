# line-filled: Filled Line Plot

## Description

A line plot with the area between the line and the baseline (typically x-axis) filled with a semi-transparent color. This creates an area chart effect for a single series, emphasizing the magnitude of values.

## Applications

- Emphasizing magnitude of values over time
- Volume or quantity visualization
- Single series with area emphasis
- Stock price or metric trends

## Data

The visualization requires:
- **X variable**: Continuous variable (often time)
- **Y variable**: Single numeric variable

Example structure:
```
X    | Value
-----|-------
0    | 10
1    | 15
2    | 12
3    | 18
...
```

## Notes

- Fill should be semi-transparent (alpha ~0.3-0.5)
- Line should be visible on top of the fill
- Fill color typically matches line color
- Baseline is usually y=0

## What a good version looks like

- A good version shows: a single line joining the values in x order, never smoothed past the points it connects, with the area between the line and the baseline filled all the way along it.
- A good version shows: the fill ending at one baseline, usually zero as the Notes say, and a value axis that includes that baseline rather than cutting the fill off above it, so the filled height stays proportional to the value.
- A good version shows: a semi-transparent fill, as the Notes ask, light enough that gridlines stay visible through it in both themes.
- A good version shows: the line drawn on top of the fill and clearly stronger than it, as the Notes ask, with the fill typically in the line's own color.
- Expected, not a defect: short-term noise, dips and plateaus, a fill that thins to almost nothing where values come near the baseline, and no legend for a single series, because the axis label names the quantity.
