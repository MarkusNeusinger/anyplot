# box-grouped: Grouped Box Plot

## Description

A grouped box plot displays multiple box plots side-by-side within each category, enabling comparison of distributions across subgroups. Each group contains boxes representing different subcategories or conditions, making it ideal for multi-factor comparisons and A/B testing scenarios with multiple metrics.

## Applications

- Comparing treatment effects across different patient demographics in clinical trials
- A/B testing with multiple metrics (conversion rate, time on site) across user segments
- Analyzing performance distributions by department and experience level
- Comparing experimental results across multiple factors in research studies

## Data

- `category` (string) - main group labels (x-axis categories)
- `subcategory` (string) - subgroup identifiers for side-by-side boxes
- `value` (numeric) - numerical values to plot
- Size: 20-200 points per subcategory, 2-6 categories, 2-4 subcategories

## Notes

- Display boxes side-by-side within each category with distinct colors
- Include a clear legend identifying each subcategory
- Maintain consistent box widths across all groups
- Show median line, quartile box, whiskers at 1.5*IQR, and outliers

## What a good version looks like

- A good version shows: within each category, one box per subcategory placed side by side, as the Notes ask, with the categories visibly set apart so each cluster of boxes reads as one group.
- A good version shows: each subcategory in its own distinct color, the same in every category, and a legend naming each subcategory, as the Notes ask.
- A good version shows: boxes of one width across all groups, as the Notes ask, on one shared value axis that is not forced to zero.
- A good version shows: each box spanning the first to the third quartile with a median line visible against the fill in both themes, whiskers reaching to the most extreme values within 1.5 times the IQR, and values beyond them as individual points at their values, as the Notes ask.
- Expected, not a defect: outlier points beyond the whiskers, boxes of very different length and position inside one category, whiskers of unequal length, and neighboring boxes whose value ranges overlap; they are the comparison the chart exists to show.
