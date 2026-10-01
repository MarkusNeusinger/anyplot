# bar-stacked-percent: 100% Stacked Bar Chart

## Description

A 100% stacked bar chart displays multiple data series as proportional segments within each bar, where every bar is normalized to sum to 100%. This visualization emphasizes composition and relative proportions rather than absolute values, making it ideal for comparing how different components contribute to a whole across categories. It reveals patterns in distribution and share that might be obscured when absolute values vary significantly between categories.

## Applications

- Tracking market share evolution over time where each bar represents a time period and segments show competitor proportions
- Analyzing survey response distributions where each question's responses are shown as percentage breakdowns
- Comparing budget or resource allocation across departments where each bar shows proportional spending by category

## Data

- `category` (categorical) - Labels for each bar on the x-axis (e.g., years, regions, departments)
- `component` (categorical) - The different series being compared (creates the proportional segments)
- `value` (numeric) - Raw values that will be normalized to percentages within each category
- Size: 3-12 categories with 2-6 components recommended for clear interpretation
- Example: Market share by quarter, survey responses by question, energy mix by country

## Notes

- Use distinct, harmonious colors for each component with a clear legend
- Consider adding percentage labels within segments when space permits
- Order components consistently across all bars for easier visual tracking
- Ensure the legend clearly identifies each component
- This variant is preferred over regular stacked bars when comparing proportions matters more than absolute values

## What a good version looks like

- A good version shows: every bar the same full length, from zero to the whole, with each segment starting where the previous one ends and its length equal to that component's share of its own category's total.
- A good version shows: a value axis read as percentage of the total, running from zero to the whole and never truncated, so the chart shows relative proportions and not absolute values.
- A good version shows: the components in the same order in every bar, as the Notes ask, so one component can be followed across the categories.
- A good version shows: one distinct color per component, the same in every bar, and a legend that identifies each component, as the Notes ask, with neighboring segments distinguishable in both themes.
- A good version shows: percentage labels, if drawn, inside segments large enough to hold them, matching each segment's share and readable against their own fill in both themes.
- Expected, not a defect: thin slivers for small shares that are left unlabeled, inner boundaries that shift from bar to bar because the segments before them changed, rounded labels that miss the whole by a point, and no sign of the absolute totals, which this chart does not show.
