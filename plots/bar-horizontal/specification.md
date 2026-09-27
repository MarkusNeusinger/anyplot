# bar-horizontal: Horizontal Bar Chart

## Description

A horizontal bar chart displaying categorical data with rectangular bars extending horizontally from the y-axis. The length of each bar is proportional to the value it represents. This orientation is particularly effective when category names are long or numerous, as horizontal labels are easier to read than rotated vertical labels. Horizontal bar charts excel at rankings, comparisons, and survey results visualization.

## Applications

- Displaying survey results with descriptive response options
- Showing ranked lists such as top products, countries by population, or employee performance
- Creating population pyramid base charts for demographic analysis

## Data

- `category` (categorical) - Labels for each bar on the y-axis
- `value` (numeric) - Length of the bars representing the measured quantity
- Size: 5-20 categories recommended for readability
- Example: Survey response counts, country statistics, product performance metrics

## Notes

- Bar heights should be consistent across all categories
- Consider sorting bars by value for easier comparison (largest to smallest or vice versa)
- Use a single color for all bars, or highlight specific bars to draw attention
- Ensure adequate spacing between bars for visual clarity
- Value labels can be placed at the end of bars or inside them

## What a good version looks like

- A good version shows: one horizontal bar per category extending from a zero baseline, so bar length stays proportional to the value, on a value axis that is never truncated.
- A good version shows: bars of one thickness with even gaps, and categories in a meaningful order: by value for a ranking, or their natural order (response scales, age groups) when they have one.
- A good version shows: each category label written horizontally beside its bar and shown in full, with long labels given room rather than truncated or rotated.
- A good version shows: one color for all bars, or an accent color on the bars the scenario highlights, as the Notes allow.
- A good version shows: value labels, if drawn, at the bar ends or inside the bars, readable in both themes and not colliding with each other.
- Expected, not a defect: unequal lengths, including one dominant or one near-empty bar and a long tail of short bars; they are the point of the chart, not an imbalance to fix.
