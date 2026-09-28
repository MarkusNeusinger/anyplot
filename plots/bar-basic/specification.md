# bar-basic: Basic Bar Chart

## Description

A vertical bar chart that displays categorical data with rectangular bars whose heights are proportional to the values they represent. This fundamental visualization is ideal for comparing discrete categories and identifying which categories have the highest or lowest values. Bar charts excel at showing rankings, distributions across categories, and making relative comparisons intuitive.

## Applications

- Comparing quarterly sales figures across different product lines
- Visualizing survey responses showing preference counts for different options
- Displaying population statistics across different age groups or regions

## Data

- `category` (categorical) - Labels for each bar on the x-axis
- `value` (numeric) - Heights of the bars representing the measured quantity
- Size: 3-15 categories recommended for readability
- Example: Product sales by category, survey response counts, performance metrics by department

## Notes

- Bar widths should be consistent across all categories
- Consider adding value labels on or above bars for precise reading
- Use a single color for all bars, or highlight specific bars to draw attention
- Ensure adequate spacing between bars for visual clarity

## What a good version looks like

- A good version shows: one vertical bar per category rising from a zero baseline, so bar height stays proportional to the value, on a value axis that is never truncated.
- A good version shows: bars of one width with even gaps, and categories in a meaningful order: by value, or their natural order (months, age groups) when they have one.
- A good version shows: the basic variant's emphasis only: one color for all bars, or an accent color on a bar or two as the Notes allow, and no reference or average lines, highlight bands, callouts, error bars, stacking, grouping or trend line.
- A good version shows: value labels, if drawn, clear of the bar ends, readable in both themes and not colliding with each other.
- Expected, not a defect: unequal heights, including one dominant or one near-empty bar; they are the point of the chart, not an imbalance to fix.
