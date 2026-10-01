# violin-split: Split Violin Plot

## Description

A split violin plot displaying two distributions side-by-side within each violin, with each half representing a different group. Unlike standard violin plots that mirror the same distribution, split violins use the left and right halves to compare two conditions (such as before/after, male/female, or control/treatment) at each category level. This enables direct visual comparison of distribution shapes between paired groups.

## Applications

- Comparing patient outcomes before and after treatment across multiple clinics
- Analyzing salary distributions by gender across job categories
- Comparing test score distributions between control and experimental groups
- Visualizing seasonal patterns (summer vs winter) across different regions

## Data

- `category` (string) - group labels for the x-axis (e.g., department, region)
- `value` (numeric) - numerical values to plot as distributions
- `split_group` (string/binary) - binary grouping variable for left/right halves
- Size: 30-500 points per category per split group, 2-6 categories

## Notes

- Use distinct colors for each split group with legend
- Ensure the two halves meet at the center line
- Consider adding inner box plot or quartile markers
- Alpha transparency helps when distributions overlap at center

## What a good version looks like

- A good version shows: for each category one violin made of two half densities, one split group on each side of a shared center line, each half the density of its own group rather than a mirror of the other.
- A good version shows: the two halves meeting at the center line, as the Notes ask, with the same split group on the same side in every category.
- A good version shows: a distinct color for each split group, the same in every category, and a legend naming the two groups, as the Notes ask.
- A good version shows: an inner box plot or quartile markers, if drawn as the Notes suggest, at the quartiles of the half they describe and visible against the fill in both themes.
- A good version shows: one shared value axis for all violins that is not forced to zero, with each half's tails ending near its data range instead of trailing far beyond it.
- Expected, not a defect: lopsided violins whose two halves differ in width, length and shape, peaks and medians at different positions on the two sides, and multimodal or skewed halves; the asymmetry is the comparison the chart exists to show.
