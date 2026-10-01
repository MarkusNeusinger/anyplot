# pie-basic: Basic Pie Chart

## Description

A pie chart showing proportions of categorical data as slices of a circle. Each slice represents a category's contribution to the whole, with the angle proportional to its value. Essential for visualizing parts-to-whole relationships in a simple, intuitive format.

## Applications

- Market share distribution across competitors
- Budget allocation by department
- Survey response breakdown
- Resource utilization by category

## Data

- `category` (string) - category labels
- `value` (numeric) - values for each category
- Size: 3-8 categories (too many becomes unreadable)
- Values must be positive and sum to a meaningful whole
- Example: Market share of 5-6 tech companies

## Notes

- Include percentage labels on slices
- Use distinct colors for each category
- Add a legend for category identification
- Slightly explode the largest or smallest slice for emphasis

## What a good version looks like

- A good version shows: one slice per category in a round, undistorted circle, each slice's angle proportional to its value and the slices together closing the full circle; position is angle, not data, so there are no axes or grid.
- A good version shows: a percentage label for every slice, as the Notes ask, matching the slice's share, on the slice or beside it with a leader line where the slice is narrow, readable in both themes and not colliding with other labels.
- A good version shows: one distinct color per slice and a legend that names the categories, as the Notes ask, with neighboring slices distinguishable in both themes.
- A good version shows: the largest or the smallest slice pulled slightly out of the circle for emphasis, as the Notes ask, while the other slices stay joined.
- A good version shows: the basic variant's single flat pie: besides the one exploded slice the Notes ask for, no hollow center, second pie or ring, tilted or three-dimensional view, reference lines, further highlighted slices or bands, or callouts beyond the slice labels.
- Expected, not a defect: slices of very different size, including one dominant slice and a thin sliver whose label sits outside it, and a small offset gap around the exploded slice.
