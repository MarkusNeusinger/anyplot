# area-stacked: Stacked Area Chart

## Description

A stacked area chart displays multiple data series as areas stacked on top of each other, with each series starting where the previous one ends. This visualization emphasizes both individual contributions and cumulative totals over a continuous axis (typically time). It is ideal for showing how parts contribute to a whole while tracking changes over time, making patterns of composition and overall trends immediately visible.

## Applications

- Revenue breakdown by product line over time
- Website traffic sources (direct, organic, referral, social) over months
- Resource allocation across departments or projects
- Energy consumption by sector over years

## Data

- `x` (datetime/numeric) - continuous axis values, typically time periods
- `y1, y2, y3, ...` (numeric) - values for each series to be stacked
- `category` (categorical) - labels identifying each series
- Size: 10-100 time points, 2-8 series
- Example: monthly revenue by product category over two years

## Notes

- Use distinct but harmonious colors for each series
- Order series by size (largest at bottom) for easier reading
- Include legend to identify each series
- Consider using semi-transparent fills for overlapping visibility
- Ensure baseline starts at zero to avoid misleading proportions

## What a good version looks like

- A good version shows: each series as a filled layer that starts where the layer below ends, with no gaps between layers, so a layer's thickness at any x is its value and the top edge of the stack is the total.
- A good version shows: the lowest layer rising from a zero baseline, as the Notes ask, on a value axis that is never truncated and reaches past the highest total.
- A good version shows: the layers in the same order at every x, ordered by size with the largest at the bottom, as the Notes ask.
- A good version shows: one distinct color per series, the same along the whole axis and named in a legend, with neighboring layers distinguishable in both themes; semi-transparent fills, if used, still match their legend entries.
- Expected, not a defect: thin layers for small series, upper layers whose edges rise and fall with the layers beneath them even when their own values are steady, and a total that varies along the axis.
