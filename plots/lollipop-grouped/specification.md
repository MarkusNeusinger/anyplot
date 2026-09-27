# lollipop-grouped: Grouped Lollipop Chart

## Description

A grouped lollipop chart displays multiple series across categorical variables using thin stems and circular markers arranged in groups. Each category has multiple lollipops side by side, one for each series, enabling direct comparison of metrics across groups. It combines the clarity of dot plots with the organization of grouped bar charts while reducing visual clutter.

## Applications

- Comparing sales performance across regions for multiple product lines
- Survey results showing scores for different questions across demographic groups
- Performance metrics (accuracy, speed, cost) across different algorithms or models
- Year-over-year comparisons of multiple KPIs across departments

## Data

- `category` (string) - Categorical labels for grouping (e.g., regions, departments)
- `series` (string) - Series identifier distinguishing each lollipop within a group
- `value` (numeric) - The measurement or count for each category-series combination
- Size: 3-8 categories with 2-5 series for optimal readability
- Example: Quarterly revenue by product line across 4 regions

## Notes

- Stems should be thin lines connecting baseline to marker
- Markers should be circular dots with distinct colors for each series
- Lollipops within a group should be positioned side by side with slight offset
- Include a legend to identify series colors
- Consider horizontal orientation if category labels are long
- Sort categories by a meaningful metric to reveal patterns

## What a good version looks like

- A good version shows: every lollipop as a thin stem from one shared zero baseline to a circular marker at its value, on a value axis that is never truncated, so stem lengths compare directly within a category and across categories.
- A good version shows: each category's lollipops side by side with a slight offset as one group, a wider gap between groups than within them, and the series in the same order in every group.
- A good version shows: one distinct color per series, the same in every group and named in a legend, so each series can be followed across the categories.
- A good version shows: categories in a meaningful order: sorted by a metric such as their total, or their natural order when they have one, with horizontal lollipops when category labels are long.
- Expected, not a defect: markers of neighboring series at nearly the same height, series that swap rank from one category to the next, and very short stems for values near zero; they are the point of the chart, not an imbalance to fix.
