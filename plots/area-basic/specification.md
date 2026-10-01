# area-basic: Basic Area Chart

## Description

An area chart showing quantitative data over a continuous axis with the area below the line filled. It emphasizes the magnitude of values over time by filling the space between the line and axis, creating visual weight that helps readers understand volume and trends. Particularly effective for showing cumulative totals, resource consumption, or any data where the "amount" is as important as the trend.

## Applications

- Website traffic over time showing visitor volume
- Revenue trends with cumulative effect visualization
- Stock price movements with volume emphasis
- Resource utilization (CPU, memory) over time

## Data

- `x` (datetime/numeric) - continuous axis values, typically time
- `y` (numeric) - values to plot representing magnitude
- Size: 20-500 data points
- Example: daily website visitors over a month

## Notes

- Use semi-transparent fill (alpha 0.3-0.5) for better readability
- Include gridlines for value estimation
- Add clear axis labels with units
- Consider gradient fill from bottom to line for visual appeal

## What a good version looks like

- A good version shows: one line joining the values in x order, never smoothed past them, with the area between that line and the baseline filled at every x, so the top edge is the series and the filled area reads as quantity.
- A good version shows: a value axis that starts at zero, so the height of the fill stays proportional to the value it stands for.
- A good version shows: a semi-transparent fill under a solid top edge, as the Notes ask, so the gridlines the Notes ask for stay visible through the area in both themes; a gradient fading from the line toward the baseline, if used, keeps the top edge distinct.
- A good version shows: the basic variant's single filled series: no second series or stacking, trend or reference and mean lines, shaded or highlight bands, highlighted points, or callouts and event annotations.
- Expected, not a defect: short-term noise, dips and spikes along the top edge, a fill paler than its edge line, and no legend for a single series, because the axis label names the quantity.
