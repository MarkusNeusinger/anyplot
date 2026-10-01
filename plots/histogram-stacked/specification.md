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

## What a good version looks like

- A good version shows: in each bin, one segment per group stacked directly on the next with no gaps, the lowest rising from a zero baseline, so a segment's height is its group's frequency in the bin and the bar top is the combined frequency.
- A good version shows: the same bin boundaries for all groups, as the Notes ask, with contiguous bars on a frequency axis that is never truncated and reaches past the tallest total.
- A good version shows: one distinct color per group, the same in every bin and named in a legend, as the Notes ask, with neighboring segments distinguishable in both themes.
- A good version shows: a segment order the reader can follow: one order kept in every bin, or the groups ordered by size as the Notes suggest.
- Expected, not a defect: thin or missing segments where a group has few or no observations, upper segments that start at different heights from bin to bin, and lumpy totals with empty bins in the tails.
