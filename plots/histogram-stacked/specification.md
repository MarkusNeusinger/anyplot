# histogram-stacked: Stacked Histogram

## Description

A histogram showing multiple groups stacked on top of each other within each bin. The total bar height represents the combined frequency, while colored segments show individual group contributions.

## Applications

- Comparing distributions of multiple groups
- Showing composition within histogram bins
- Total frequency with group breakdown
- Demographic or categorical comparisons

## Data

- `values` (continuous numeric) - Quantitative data to be binned and aggregated
- `group` (categorical) - Group or category label for stacking segments

Example structure:
```
values | group
-------|-------
12.5   | A
18.3   | B
15.7   | A
22.1   | B
14.2   | C
```

- Size: 50-5000 points recommended (more points provide better distribution resolution)
- Example: Sales amounts per product category, test scores by demographic group

## Notes

- Same bin boundaries applied to all groups
- Distinct colors for each group
- Legend shows group labels
- Total bar height = combined frequency
- Consider ordering groups by size within bins
