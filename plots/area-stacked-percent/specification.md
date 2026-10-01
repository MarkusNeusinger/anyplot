# area-stacked-percent: 100% Stacked Area Chart

## Description

A stacked area chart normalized to 100%, where each area represents the percentage contribution of a category to the total. The combined height always equals 100%, showing proportional changes over time.

## Applications

- Market share evolution over time
- Portfolio composition changes
- Budget allocation trends
- Demographic proportion shifts

## Data

- `time` (continuous) - X-axis variable representing temporal progression (dates, years, or time periods)
- `category` (categorical) - Identifies each stacked area (e.g., product, region, segment name)
- `value` (numeric) - Raw count or amount for each category; automatically normalized to percentage within each time point
- Size: 50–5000 points (10–100 time periods × 5–50 categories)
- Example: Monthly revenue by product line (12 months × 5 products = 60 rows)

Example structure:
```
Time | Category   | Value
-----|------------|-------
2020 | Product A  | 400
2020 | Product B  | 350
2020 | Product C  | 250
2021 | Product A  | 450
2021 | Product B  | 300
2021 | Product C  | 250
```

## Notes

- Total always equals 100%
- Shows relative proportions, not absolute values
- Good for composition changes over time
- Each area width shows percentage contribution

## What a good version looks like

- A good version shows: each category as a filled layer that starts where the layer below ends, its thickness at every time point equal to its share of that time point's total.
- A good version shows: a stack that fills the full height of the percentage axis at every time point, from zero to the whole, with a flat top edge and no gap, overshoot or empty stretch.
- A good version shows: a value axis read as percentage of the total, running from zero to the whole and never truncated, so the chart shows relative proportions and not absolute values.
- A good version shows: the layers in the same order at every time point, each in one color along the whole axis and identified by a legend or by labels at the layers, with neighboring layers distinguishable in both themes.
- Expected, not a defect: thin layers for small shares, a layer that shrinks to almost nothing, inner boundaries that move because the layers beneath them changed, and no sign of growth or decline in the total, which this chart does not show.
