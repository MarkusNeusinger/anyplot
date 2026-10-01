# bar-stacked: Stacked Bar Chart

## Description

A stacked bar chart that displays multiple data series stacked on top of each other within each category, showing both individual component values and their cumulative totals. This visualization excels at revealing part-to-whole relationships while maintaining the ability to compare totals across categories. Stacked bar charts are particularly effective for composition analysis, where understanding how different components contribute to a whole is as important as comparing totals.

## Applications

- Analyzing budget allocations across departments showing expense categories as stacked components
- Visualizing revenue composition over time with different product lines or regions stacked
- Displaying survey responses where multiple answer options are stacked to show total respondents per question

## Data

- `category` (categorical) - Labels for each bar on the x-axis (e.g., months, regions, products)
- `component` (categorical) - The different series being stacked (creates the segments within each bar)
- `value` (numeric) - Size of each segment representing the measured quantity
- Size: 3-10 categories with 2-6 stacked components recommended for readability
- Example: Monthly sales by product category, expense breakdown by department, energy consumption by source

## Notes

- Use distinct, harmonious colors for each stacked component with a clear legend
- Consider adding total value labels above each complete stack
- Order components consistently across all bars (largest at bottom or by logical grouping)
- Ensure adequate spacing between bars for visual clarity
- For precise segment comparisons, consider using a grouped bar chart instead

## What a good version looks like

- A good version shows: one stack per category rising from a shared zero baseline, each segment starting where the one below it ends, so a segment's height is its value and the top of the stack is the category total, on a value axis that is never truncated.
- A good version shows: the components in the same order in every bar, with the largest at the bottom or in a logical grouping, as the Notes ask.
- A good version shows: one distinct color per component, the same in every bar and named in a legend, with neighboring segments distinguishable in both themes.
- A good version shows: bars of one width with even gaps between them, so each stack reads as one category.
- A good version shows: total labels, if drawn, above each complete stack and equal to the sum of its segments, readable in both themes and not colliding with each other.
- Expected, not a defect: stacks of unequal height, thin segments for small components, and upper segments that start at different heights from bar to bar because the segments beneath them differ.
