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

- One vertical bar per category rising from a zero baseline, so bar height stays proportional to the value; the value axis is never truncated.
- Bars share one width and even gaps, and categories follow a meaningful order — by value, or their natural order (months, age groups) when they have one.
- One colour for all bars is correct; highlighting one or two bars in an accent colour, as the Notes allow, is the only emphasis the basic variant needs.
- Value labels are optional; when present they sit clear of the bar ends, stay readable in both themes and do not collide with each other.
- Unequal heights, including one dominant or one near-empty bar, are the point of the chart, not an imbalance to fix; the basic variant adds no error bars, stacking, grouping or trend line.
