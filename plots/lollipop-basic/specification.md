# lollipop-basic: Basic Lollipop Chart

## Description

A lollipop chart displays categorical data with thin lines (stems) extending from a baseline to circular markers (dots) at each data point. It presents the same information as a bar chart but with a cleaner, more minimalist aesthetic that reduces visual clutter while maintaining clear value comparisons.

## Applications

- Ranking top performers across categories (e.g., sales by region, employee scores)
- Survey results with many response categories where bars would look cluttered
- Year-over-year or period comparisons with discrete categories
- Displaying sorted metrics where the relative position and exact value both matter

## Data

- `category` (string) - Categorical labels for each data point
- `value` (numeric) - The measurement or count for each category
- Size: 5-20 categories for optimal readability
- Example: Product sales by category, sorted by value

## Notes

- Stems should be thin lines connecting baseline to marker
- Markers should be circular dots clearly visible at data values
- Vertical orientation preferred (categories on x-axis, values on y-axis)
- Data sorted by value improves readability
- Consider horizontal orientation if category labels are long

## What a good version looks like

- A good version shows: one thin stem per category from a zero baseline to a circular marker at the value, so stem length stays proportional to the value, on a value axis that is never truncated.
- A good version shows: stems clearly thinner than the markers, so each category reads as a dot on a stick rather than a thin bar, with stems and markers visible in both themes.
- A good version shows: categories in a meaningful order: by value, as the Notes suggest, or their natural order when they have one, with vertical stems, or horizontal ones when category labels are long.
- A good version shows: the basic variant's single series: one color for all stems and markers, and no second series, error bars, mean or reference line, value-dependent coloring or callouts.
- Expected, not a defect: stems of very different lengths, including one dominant value and one near zero whose marker sits almost on the baseline; they are the point of the chart, not an imbalance to fix.
