# bar-stacked-labeled: Stacked Bar Chart with Total Labels

## Description

A stacked bar chart that displays multiple data series stacked on top of each other with total value labels prominently shown above each bar stack. This variant combines part-to-whole visualization with explicit numerical annotations, making it easy to read both individual segment contributions and cumulative totals at a glance. The total labels eliminate the need for mental arithmetic when comparing overall values across categories.

## Applications

- Comparing quarterly sales by product line with clear total revenue figures for executive presentations
- Displaying project budget breakdowns by task category with visible total costs for each project phase
- Visualizing survey response distributions with total respondent counts labeled for each question

## Data

- `category` (categorical) - Labels for each bar group on the x-axis (e.g., quarters, departments, regions)
- `component` (categorical) - The different series being stacked within each bar (e.g., product lines, cost types)
- `value` (numeric) - Size of each segment representing the measured quantity
- Size: 3-8 categories with 2-5 stacked components recommended for readability
- Example: Quarterly revenue by product category, department expenses by cost type

## Notes

- Total labels should be placed directly above each complete bar stack with clear formatting
- Use a consistent number format for labels (e.g., rounded integers, one decimal place, or with units)
- Ensure adequate vertical space above the tallest bar for label placement
- Consider using a slightly larger or bold font for total labels to distinguish from segment labels
- Segment labels within the bars are optional but can enhance readability for larger segments

## What a good version looks like

- A good version shows: one stack per category rising from a shared zero baseline, each segment starting where the one below it ends, so a segment's height is its value and the top of the stack is the category total, on a value axis that is never truncated.
- A good version shows: a total label directly above every complete stack, as the Notes ask, equal to the sum of that stack's segments and readable in both themes.
- A good version shows: a value axis with room above the tallest stack, as the Notes ask, so its total label sits inside the plot area and is not clipped.
- A good version shows: every label in one number format, as the Notes ask, and segment labels, if drawn, inside segments large enough to hold them and readable against their own fill in both themes.
- A good version shows: one distinct color per component, the same in every bar and named in a legend or by direct labels, with the components in the same order in every stack.
- Expected, not a defect: stacks of unequal height, thin segments for small components whose segment label is left out, and upper segments that start at different heights from bar to bar because the segments beneath them differ.
