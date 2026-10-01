# histogram-overlapping: Overlapping Histograms

## Description

Overlapping histograms display multiple distributions on the same axes using semi-transparent bars, enabling direct visual comparison between groups. This technique reveals differences in central tendency, spread, and shape across categories while maintaining the familiar histogram format. The transparency allows viewers to see where distributions overlap and diverge.

## Applications

- Comparing test score distributions between control and treatment groups in A/B testing
- Analyzing salary distributions across different departments or job levels
- Visualizing before/after measurement changes in clinical trials or process improvements

## Data

- `values` (numeric) - The continuous variable to visualize
- `group` (categorical) - The grouping variable distinguishing each distribution
- Size: 30-500 observations per group recommended; 2-4 groups work best
- Example: Heights by gender, response times by condition, prices by region

## Notes

- Use semi-transparent fills (alpha ~0.4-0.6) so overlapping regions remain visible
- Assign distinct, contrasting colors to each group
- Include a legend clearly identifying each group
- Align bin edges across all groups for accurate comparison
- Consider using matching bin widths and counts for all distributions

## What a good version looks like

- A good version shows: one histogram per group on the same axes, every group's bars rising from the same zero baseline rather than stacked or placed side by side, so each bar's height is that group's own value for the bin.
- A good version shows: semi-transparent fills, as the Notes ask, so every group's bars stay visible where the distributions overlap, including the group drawn behind, in both themes.
- A good version shows: one distinct, contrasting color per group, named in a legend, as the Notes ask.
- A good version shows: bin edges aligned across all groups, as the Notes ask, so bars of different groups cover the same intervals.
- Expected, not a defect: blended colors where groups overlap that match no legend entry, groups of different height and spread, distributions that overlap almost fully or hardly at all, and lumpy outlines.
